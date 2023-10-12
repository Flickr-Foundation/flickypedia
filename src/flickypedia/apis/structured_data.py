"""
Create structured data entities for display on Wikimedia Commons.

This creates statements that will be passed in the list of statements
sent in the ``data`` parameter of the ``wbeditentity`` API.

If you want to understand how we create our structured data, it might
be helpful to look at the files in 'tests/fixtures/structured_data' --
that folder contains examples of the JSON we'll send to the API.

== Useful reading ==

*   Commons:Flickypedia/Data Modeling
    https://commons.wikimedia.org/wiki/Commons:Flickypedia/Data_Modeling

"""

import datetime

from flickypedia.apis.flickr import TakenDateGranularity
from flickypedia.apis.wikidata import (
    lookup_flickr_user_in_wikidata,
    to_wikidata_date,
    WikidataEntities,
    WikidataProperties,
)


def _wikibase_entity_value(*, property_id, entity_id):
    return {
        "snaktype": "value",
        "property": property_id,
        "datavalue": {
            "type": "wikibase-entityid",
            "value": {"id": entity_id},
        },
    }


def _create_qualifiers(qualifier_values):
    result = {}

    for qualifier in qualifier_values:
        property_id = qualifier["property"]

        if qualifier.keys() == {"property", "value"}:
            result[property_id] = [
                {
                    "datavalue": {"type": "string", "value": qualifier["value"]},
                    "property": property_id,
                    "snaktype": "value",
                }
            ]
        elif qualifier.keys() == {"property", "entity_id"}:
            result[property_id] = [
                _wikibase_entity_value(
                    property_id=property_id, entity_id=qualifier["entity_id"]
                )
            ]
        elif qualifier.keys() == {"property", "date", "precision"}:
            result[property_id] = [
                {
                    "datavalue": to_wikidata_date(
                        qualifier["date"], precision=qualifier["precision"]
                    ),
                    "property": property_id,
                    "snaktype": "value",
                }
            ]
        # This should never happen in practice, but we add an ``else:``
        # with a meaningful error message in case it ever occurs.
        #
        # We don't need to test this branch because it's only a function
        # used in this file, not externally.
        else:  # pragma: no cover
            raise ValueError(f"Unrecognised qualifier value: {qualifier!r}")

    return result


def create_flickr_creator_data(user_id, username, realname):
    """
    Create a structured data statement for a user on Flickr.

    This is either:

    *   A link to the corresponding Wikidata entity, or
    *   A collection of values that link to their profile page

    """
    wikidata_id = lookup_flickr_user_in_wikidata(id=user_id, username=username)

    if wikidata_id is not None:
        return {
            "mainsnak": _wikibase_entity_value(
                property_id=WikidataProperties.Creator, entity_id=wikidata_id
            ),
            "type": "statement",
        }
    else:
        qualifier_values = [
            {"property": WikidataProperties.AuthorName, "value": realname or username},
            {
                "property": WikidataProperties.Url,
                "value": f"https://www.flickr.com/photos/{user_id}/",
            },
            {"property": WikidataProperties.FlickrUserId, "value": user_id},
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


def create_copyright_status_data(status):
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


def create_source_data_for_photo(user_id, photo_id, jpeg_url):
    """
    Create a structured data statement for a Flickr photo.

    TODO: The mapping document mentions adding Identifier -> Flickr Photo ID

    TODO: The mapping document mentions adding a category for
    'Uploaded by Flickypedia'.  That's not supported here, but we should
    consider it.
    """
    qualifier_values = [
        {
            "property": WikidataProperties.DescribedAtUrl,
            "value": f"https://www.flickr.com/photos/{user_id}/{photo_id}/",
        },
        {"property": WikidataProperties.Operator, "entity_id": WikidataEntities.Flickr},
        {"property": WikidataProperties.Url, "value": jpeg_url},
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


def create_license_statement(license_id):
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


def create_uploaded_to_flickr_statement(uploaded_date: datetime.datetime):
    """
    Create a structured data statement for date uploaded to Flickr.
    """
    qualifier_values = [
        {
            "property": WikidataProperties.PublicationDate,
            "date": uploaded_date,
            "precision": "day",
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


def create_date_taken_statement(date_taken: datetime.datetime, taken_granularity: int):
    """
    Create a structured data statement for date taken.

    In most cases this is a single value with a precision attached, but
    for dates which are marked as "circa" on Flickr, we add an additional
    "circa" qualifier.

    Here ``granularity`` comes from the Flickr API: see "Photo Dates".
    https://www.flickr.com/services/api/misc.dates.html
    """
    try:
        precision = {
            TakenDateGranularity.Day: "day",
            TakenDateGranularity.Month: "month",
            TakenDateGranularity.Year: "year",
            TakenDateGranularity.Circa: "year",
        }[taken_granularity]
    except KeyError:
        raise ValueError(f"Unrecognised taken_granularity: {taken_granularity!r}")

    if taken_granularity in {
        TakenDateGranularity.Day,
        TakenDateGranularity.Month,
        TakenDateGranularity.Year,
    }:
        return {
            "mainsnak": {
                "datavalue": to_wikidata_date(date_taken, precision=precision),
                "property": WikidataProperties.Inception,
                "snaktype": "value",
            },
            "type": "statement",
        }
    else:
        assert taken_granularity == TakenDateGranularity.Circa

        qualifier_values = [
            {
                "property": WikidataProperties.SourcingCircumstances,
                "entity_id": WikidataEntities.Circa,
            },
        ]

        return {
            "mainsnak": {
                "datavalue": to_wikidata_date(date_taken, precision=precision),
                "property": WikidataProperties.Inception,
                "snaktype": "value",
            },
            "qualifiers": _create_qualifiers(qualifier_values),
            "qualifiers-order": [WikidataProperties.SourcingCircumstances],
            "type": "statement",
        }
