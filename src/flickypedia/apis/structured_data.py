"""
Functions for creating structured data entities for use with the
Wikimedia APIs.

The goal of this file is to create some helpers and templates to reduce
the amount of repetition required when creating these entities.
"""

from flickypedia.apis.wikidata import (
    lookup_flickr_user_in_wikidata,
    WikidataEntities,
    WikidataProperties,
)


def _wikibase_entity_value(*, property, wikidata_id):
    return {
        "snaktype": "value",
        "property": property,
        "datavalue": {
            "type": "wikibase-entityid",
            "value": {"id": wikidata_id},
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
                {
                    "datavalue": {
                        "type": "wikibase-entityid",
                        "value": {"id": qualifier["entity_id"]},
                    },
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
    Create a structured data claim for a user on Flickr.

    This is either:

    *   A link to the corresponding Wikidata entity, or
    *   A collection of values that link to their profile page

    """
    wikidata_id = lookup_flickr_user_in_wikidata(id=user_id, username=username)

    if wikidata_id is not None:
        return {
            "mainsnak": _wikibase_entity_value(
                property=WikidataProperties.Creator, wikidata_id=wikidata_id
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
    Create a structured data claim for a copyright status.

    Currently this only supports "Copyright status: copyrighted", but
    it might evolve in future if we e.g. support "no known copyright status".
    """
    if status != "copyrighted":
        raise ValueError(
            f"Unable to map a copyright status which isn't “copyrighted”: {status!r}"
        )

    return {
        "mainsnak": _wikibase_entity_value(
            property=WikidataProperties.CopyrightStatus,
            wikidata_id=WikidataEntities.Copyrighted,
        ),
        "type": "statement",
    }


def create_source_data_for_photo(user_id, photo_id, jpeg_url):
    """
    Create a structured data claim for a Flickr photo.

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
            property=WikidataProperties.SourceOfFile,
            wikidata_id=WikidataEntities.FileAvailableOnInternet,
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
            property=WikidataProperties.CopyrightLicense,
            wikidata_id=wikidata_license_id,
        ),
        "type": "statement",
    }
