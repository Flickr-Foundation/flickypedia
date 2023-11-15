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

*   Commons:Structured data/Modeling
    https://commons.wikimedia.org/wiki/Commons:Structured_data/Modeling

"""

import datetime
from typing import List, Optional

from flickr_photos_api import DateTaken, LocationInfo, User as FlickrUser, SinglePhoto

from flickypedia.apis.flickr_user_ids import lookup_flickr_user_in_wikidata
from ._qualifiers import create_qualifiers as create_qualifiers, QualifierValues
from ._types import NewStatement, NewClaims
from .wikidata import (
    to_wikidata_date_value,
    to_wikidata_entity_value,
    WikidataEntities,
    WikidataProperties,
)


def create_flickr_creator_statement(user: FlickrUser) -> NewStatement:
    """
    Create a structured data statement for a user on Flickr.

    This is either:

    *   A link to the corresponding Wikidata entity, or
    *   A collection of values that link to their profile page

    """
    wikidata_id = lookup_flickr_user_in_wikidata(user)

    if wikidata_id is not None:
        return {
            "mainsnak": {
                "snaktype": "value",
                "property": WikidataProperties.Creator,
                "datavalue": to_wikidata_entity_value(entity_id=wikidata_id),
            },
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
            "qualifiers": create_qualifiers(qualifier_values),
            "qualifiers-order": [
                WikidataProperties.FlickrUserId,
                WikidataProperties.AuthorName,
                WikidataProperties.Url,
            ],
            "type": "statement",
        }


def create_copyright_status_statement(license_id: str) -> NewStatement:
    """
    Create a structured data statement for a copyright status.
    """
    if license_id in {"cc-by-2.0", "cc-by-sa-2.0"}:
        return {
            "mainsnak": {
                "snaktype": "value",
                "property": WikidataProperties.CopyrightStatus,
                "datavalue": to_wikidata_entity_value(
                    entity_id=WikidataEntities.Copyrighted
                ),
            },
            "type": "statement",
        }
    elif license_id == "usgov":
        qualifier_values: List[QualifierValues] = [
            {
                "property": WikidataProperties.AppliesToJurisdiction,
                "entity_id": WikidataEntities.UnitedStatesOfAmerica,
                "type": "entity",
            },
            {
                "property": WikidataProperties.DeterminationMethod,
                "entity_id": WikidataEntities.WorkOfTheFederalGovernmentOfTheUnitedStates,
                "type": "entity",
            },
        ]

        return {
            "mainsnak": {
                "snaktype": "value",
                "property": WikidataProperties.CopyrightStatus,
                "datavalue": to_wikidata_entity_value(
                    entity_id=WikidataEntities.PublicDomain
                ),
            },
            "qualifiers": create_qualifiers(qualifier_values),
            "qualifiers-order": [
                WikidataProperties.AppliesToJurisdiction,
                WikidataProperties.DeterminationMethod,
            ],
            "type": "statement",
        }

    # See https://commons.wikimedia.org/wiki/Commons:Structured_data/Modeling/Copyright#Copyrighted,_dedicated_to_the_public_domain_by_copyright_holder
    elif license_id in {"cc0-1.0", "pdm"}:
        return {
            "mainsnak": {
                "snaktype": "value",
                "property": WikidataProperties.CopyrightStatus,
                "datavalue": to_wikidata_entity_value(
                    entity_id=WikidataEntities.DedicatedToPublicDomainByCopyrightOwner
                ),
            },
            "type": "statement",
        }

    # We don't map all licenses in this function -- just the licenses
    # which are accepted on Wikimedia Commons.
    #
    # In theory we should never be creating SDC for photos which can't
    # be shared on WMC; this is to give a helpful error if we do.
    else:
        raise ValueError(f"Unable to map a copyright status for license {license_id!r}")


def create_source_data_for_photo(
    photo_id: str, photo_url: str, original_url: str, retrieved_at: datetime.datetime
) -> NewStatement:
    """
    Create a structured data statement for a Flickr photo.
    """
    qualifier_values: List[QualifierValues] = [
        {
            "property": WikidataProperties.FlickrPhotoId,
            "value": photo_id,
            "type": "string",
        },
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
        {
            "property": WikidataProperties.Retrieved,
            "date": retrieved_at,
            "precision": "day",
            "type": "date",
        },
    ]

    return {
        "mainsnak": {
            "snaktype": "value",
            "property": WikidataProperties.SourceOfFile,
            "datavalue": to_wikidata_entity_value(
                entity_id=WikidataEntities.FileAvailableOnInternet
            ),
        },
        "qualifiers": create_qualifiers(qualifier_values),
        "qualifiers-order": [
            WikidataProperties.FlickrPhotoId,
            WikidataProperties.DescribedAtUrl,
            WikidataProperties.Operator,
            WikidataProperties.Url,
            WikidataProperties.Retrieved,
        ],
        "type": "statement",
    }


def create_license_statement(license_id: str) -> NewStatement:
    """
    Create a structured data statement for copyright license.
    """
    try:
        wikidata_license_id = WikidataEntities.Licenses[license_id]
    except KeyError:
        raise ValueError(f"Unrecognised license ID: {license_id!r}")

    qualifier_values: List[QualifierValues] = [
        {
            "property": WikidataProperties.DeterminationMethod,
            "entity_id": WikidataEntities.StatedByCopyrightHolderAtSourceWebsite,
            "type": "entity",
        },
    ]

    return {
        "mainsnak": {
            "snaktype": "value",
            "property": WikidataProperties.CopyrightLicense,
            "datavalue": to_wikidata_entity_value(entity_id=wikidata_license_id),
        },
        "qualifiers": create_qualifiers(qualifier_values),
        "qualifiers-order": [
            WikidataProperties.DeterminationMethod,
        ],
        "type": "statement",
    }


def create_location_statement(location: Optional[LocationInfo]) -> Optional[NewStatement]:
    """
    Creates a structured data statement for the "coordinates of
    the point of view" statement.

    This is the location of the camera, not the location of the subject.
    There were several discussions about this in the Flickr.org Slack and
    this was agreed as the most suitable.

    See https://flickrfoundation.slack.com/archives/C05AVC1JYL9/p1696947242703349
    """
    if location is None:
        return None


def create_posted_to_flickr_statement(date_posted: datetime.datetime) -> NewStatement:
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
        "mainsnak": {
            "snaktype": "value",
            "property": WikidataProperties.PublishedIn,
            "datavalue": to_wikidata_entity_value(entity_id=WikidataEntities.Flickr),
        },
        "qualifiers": create_qualifiers(qualifier_values),
        "qualifiers-order": [WikidataProperties.PublicationDate],
        "type": "statement",
    }


def create_date_taken_statement(date_taken: DateTaken) -> NewStatement:
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
                "datavalue": to_wikidata_date_value(
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
                "datavalue": to_wikidata_date_value(
                    date_taken["value"], precision=wikidata_precision
                ),
                "property": WikidataProperties.Inception,
                "snaktype": "value",
            },
            "qualifiers": create_qualifiers(qualifier_values),
            "qualifiers-order": [WikidataProperties.SourcingCircumstances],
            "type": "statement",
        }


def create_sdc_claims_for_flickr_photo(
    photo: SinglePhoto, retrieved_at: datetime.datetime
) -> NewClaims:
    """
    Creates a complete structured data claim for a Flickr photo.

    This is the main entry point into this file for the rest of Flickypedia.
    """
    creator_statement = create_flickr_creator_statement(user=photo["owner"])

    copyright_statement = create_copyright_status_statement(
        license_id=photo["license"]["id"]
    )

    # Note: the "Original" size is not guaranteed to be available
    # for all Flickr photos (in particular those who've disabled
    # downloads), but:
    #
    #   1.  We should only be calling this method with CC-licensed
    #       or public domain photos
    #   1.  Downloads are always available for those photos
    #
    original_size = [s for s in photo["sizes"] if s["label"] == "Original"][0]

    source_statement = create_source_data_for_photo(
        photo_id=photo["id"],
        photo_url=photo["url"],
        original_url=original_size["source"],
        retrieved_at=retrieved_at,
    )

    license_statement = create_license_statement(license_id=photo["license"]["id"])

    date_posted_statement = create_posted_to_flickr_statement(
        date_posted=photo["date_posted"]
    )

    statements = [
        creator_statement,
        copyright_statement,
        source_statement,
        license_statement,
        date_posted_statement,
    ]

    if not photo["date_taken"]["unknown"]:
        statements.append(create_date_taken_statement(date_taken=photo["date_taken"]))

    return {"claims": statements}
