"""
Create structured data entities for use on Wikimedia Commons.

This creates statements that will be passed in the list of statements
sent in the ``data`` parameter of the ``wbeditentity`` API.

If you want to understand how we create our structured data, it might
be helpful to look at the files in 'tests/fixtures/structured_data' --
that folder contains examples of the JSON we'll send to the API.

== Use in the rest of Flickypedia ==

The primary function is ``create_sdc_claims_for_flickr_photo()``,
which creates a list of statements which can be passed to the
``wbeditentity`` API.

This is the only function that should be used elsewhere; everything else
is supporting that function.

== Useful reading ==

*   Commons:Flickypedia/Data Modeling
    https://commons.wikimedia.org/wiki/Commons:Flickypedia/Data_Modeling

"""

import datetime
from typing import Dict, List, Literal, TypedDict, Union

from flickr_photos_api import DateTaken, User as FlickrUser, SinglePhoto

from flickypedia.apis.wikidata import (
    lookup_flickr_user_in_wikidata,
    to_wikidata_date,
    WikidataEntities,
    WikidataProperties,
)
from ._types import DataValue, Snak, Statement


def _wikibase_entity_value(*, property_id: str, entity_id: str) -> Snak:
    return {
        "snaktype": "value",
        "property": property_id,
        "datavalue": {
            "type": "wikibase-entityid",
            "value": {"id": entity_id},
        },
    }


class QualifierValueTypes:
    String = TypedDict(
        "String", {"type": Literal["string"], "property": str, "value": str}
    )
    Entity = TypedDict(
        "Entity", {"type": Literal["entity"], "property": str, "entity_id": str}
    )
    Date = TypedDict(
        "Date",
        {
            "type": Literal["date"],
            "property": str,
            "date": datetime.datetime,
            "precision": str,
        },
    )


QualifierValues = Union[
    QualifierValueTypes.String,
    QualifierValueTypes.Entity,
    QualifierValueTypes.Date,
]


def _create_qualifiers(
    qualifier_values: List[QualifierValues],
) -> Dict[str, List[Snak]]:
    result: Dict[str, List[Snak]] = {}

    for qualifier in qualifier_values:
        property_id = qualifier["property"]

        datavalue: DataValue

        if qualifier["type"] == "string":
            datavalue = {"type": "string", "value": qualifier["value"]}
        elif qualifier["type"] == "entity":
            datavalue = {
                "type": "wikibase-entityid",
                "value": {"id": qualifier["entity_id"]},
            }
        else:
            assert qualifier["type"] == "date"
            datavalue = to_wikidata_date(
                qualifier["date"], precision=qualifier["precision"]
            )

        result[property_id] = [
            {
                "datavalue": datavalue,
                "property": property_id,
                "snaktype": "value",
            }
        ]

    return result


def create_flickr_creator_statement(user: FlickrUser) -> Statement:
    """
    Create a structured data statement for a user on Flickr.

    This is either:

    *   A link to the corresponding Wikidata entity, or
    *   A collection of values that link to their profile page

    """
    wikidata_id = lookup_flickr_user_in_wikidata(
        user_id=user["id"], username=user["username"]
    )

    if wikidata_id is not None:
        return {
            "mainsnak": _wikibase_entity_value(
                property_id=WikidataProperties.Creator, entity_id=wikidata_id
            ),
            "type": "statement",
        }
    else:
        qualifier_values: List[QualifierValues] = [
            {
                "property": WikidataProperties.AuthorName,
                "value": user["realname"] or user["username"],
                "type": "string",
            },
            {
                "property": WikidataProperties.Url,
                "value": user["profile_url"],
                "type": "string",
            },
            {
                "property": WikidataProperties.FlickrUserId,
                "value": user["id"],
                "type": "string",
            },
        ]

        return {
            "mainsnak": {
                "snaktype": "somevalue",
                "property": WikidataProperties.Creator,
            },
            "qualifiers": _create_qualifiers(qualifier_values),
            "qualifiers-order": [
                WikidataProperties.FlickrUserId,
                WikidataProperties.AuthorName,
                WikidataProperties.Url,
            ],
            "type": "statement",
        }


def create_copyright_status_statement(status: str) -> Statement:
    """
    Create a structured data statement for a copyright status.

    Currently this only supports "Copyright status: copyrighted", but
    it might evolve in future if we e.g. support "no known copyright status".
    """
    if status != "copyrighted":
        raise ValueError(
            f"Unable to map a copyright status which isn't “copyrighted”: {status!r}"
        )

    return {
        "mainsnak": _wikibase_entity_value(
            property_id=WikidataProperties.CopyrightStatus,
            entity_id=WikidataEntities.Copyrighted,
        ),
        "type": "statement",
    }


def create_source_data_for_photo(photo_url: str, original_url: str) -> Statement:
    """
    Create a structured data statement for a Flickr photo.

    TODO: The mapping document mentions adding Identifier -> Flickr Photo ID

    TODO: The mapping document mentions adding a category for
    'Uploaded by Flickypedia'.  That's not supported here, but we should
    consider it.
    """
    qualifier_values: List[QualifierValues] = [
        {
            "property": WikidataProperties.DescribedAtUrl,
            "value": photo_url,
            "type": "string",
        },
        {
            "property": WikidataProperties.Operator,
            "entity_id": WikidataEntities.Flickr,
            "type": "entity",
        },
        {"property": WikidataProperties.Url, "value": original_url, "type": "string"},
    ]

    return {
        "mainsnak": _wikibase_entity_value(
            property_id=WikidataProperties.SourceOfFile,
            entity_id=WikidataEntities.FileAvailableOnInternet,
        ),
        "qualifiers": _create_qualifiers(qualifier_values),
        "qualifiers-order": [
            WikidataProperties.DescribedAtUrl,
            WikidataProperties.Operator,
            WikidataProperties.Url,
        ],
        "type": "statement",
    }


def create_license_statement(license_id: str) -> Statement:
    """
    Create a structured data statement for copyright license.
    """
    try:
        wikidata_license_id = WikidataEntities.Licenses[license_id]
    except KeyError:
        raise ValueError(f"Unrecognised license ID: {license_id!r}")

    return {
        "mainsnak": _wikibase_entity_value(
            property_id=WikidataProperties.CopyrightLicense,
            entity_id=wikidata_license_id,
        ),
        "type": "statement",
    }


def create_posted_to_flickr_statement(date_posted: datetime.datetime) -> Statement:
    """
    Create a structured data statement for date posted to Flickr.
    """
    qualifier_values: List[QualifierValues] = [
        {
            "property": WikidataProperties.PublicationDate,
            "date": date_posted,
            "precision": "day",
            "type": "date",
        },
    ]

    return {
        "mainsnak": _wikibase_entity_value(
            property_id=WikidataProperties.PublishedIn,
            entity_id=WikidataEntities.Flickr,
        ),
        "qualifiers": _create_qualifiers(qualifier_values),
        "qualifiers-order": [WikidataProperties.PublicationDate],
        "type": "statement",
    }


def create_date_taken_statement(date_taken: DateTaken) -> Statement:
    """
    Create a structured data statement for date taken.

    In most cases this is a single value with a precision attached, but
    for dates which are marked as "circa" on Flickr, we add an additional
    "circa" qualifier.

    Here ``granularity`` comes from the Flickr API: see "Photo Dates".
    https://www.flickr.com/services/api/misc.dates.html
    """
    assert not date_taken["unknown"]

    flickr_granularity = date_taken["granularity"]

    try:
        wikidata_precision = {
            "second": "day",
            "month": "month",
            "year": "year",
            "circa": "year",
        }[flickr_granularity]
    except KeyError:
        raise ValueError(f"Unrecognised taken_granularity: {flickr_granularity!r}")

    if flickr_granularity in {"second", "month", "year"}:
        return {
            "mainsnak": {
                "datavalue": to_wikidata_date(
                    date_taken["value"], precision=wikidata_precision
                ),
                "property": WikidataProperties.Inception,
                "snaktype": "value",
            },
            "type": "statement",
        }
    else:
        assert flickr_granularity == "circa"

        qualifier_values: List[QualifierValues] = [
            {
                "property": WikidataProperties.SourcingCircumstances,
                "entity_id": WikidataEntities.Circa,
                "type": "entity",
            },
        ]

        return {
            "mainsnak": {
                "datavalue": to_wikidata_date(
                    date_taken["value"], precision=wikidata_precision
                ),
                "property": WikidataProperties.Inception,
                "snaktype": "value",
            },
            "qualifiers": _create_qualifiers(qualifier_values),
            "qualifiers-order": [WikidataProperties.SourcingCircumstances],
            "type": "statement",
        }


def create_sdc_claims_for_flickr_photo(
    photo_id: str,
    photo_url: str,
    user: FlickrUser,
    copyright_status: str,
    original_url: str,
    license_id: str,
    date_posted: datetime.datetime,
    date_taken: DateTaken,
) -> List[Statement]:
    """
    Creates a complete structured data claim for a Flickr photo.

    This is the main entry point into this file for the rest of Flickypedia.
    """
    creator_statement = create_flickr_creator_statement(user)

    copyright_statement = create_copyright_status_statement(status=copyright_status)

    source_statement = create_source_data_for_photo(
        photo_url=photo_url, original_url=original_url
    )

    license_statement = create_license_statement(license_id=license_id)

    date_posted_statement = create_posted_to_flickr_statement(date_posted=date_posted)

    statements = [
        creator_statement,
        copyright_statement,
        source_statement,
        license_statement,
        date_posted_statement,
    ]

    if not date_taken["unknown"]:
        statements.append(create_date_taken_statement(date_taken))

    return statements
