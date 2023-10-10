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


def _qualifier_s(value):
    return [
        {
            "datavalue": {"type": "string", "value": value},
            "property": property_id,
            "snaktype": "value",
        }
    ]


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
        else:
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
                property=WikidataProperties.CREATOR, wikidata_id=wikidata_id
            ),
            "type": "statement",
        }
    else:
        qualifier_values = [
            {"property": WikidataProperties.AUTHOR_NAME, "value": realname or username},
            {
                "property": WikidataProperties.URL,
                "value": f"https://www.flickr.com/photos/{user_id}/",
            },
            {"property": WikidataProperties.FLICKR_USER_ID, "value": user_id},
        ]

        return {
            "mainsnak": {
                "snaktype": "somevalue",
                "property": WikidataProperties.CREATOR,
            },
            "qualifiers": _create_qualifiers(qualifier_values),
            "qualifiers-order": [
                WikidataProperties.FLICKR_USER_ID,
                WikidataProperties.AUTHOR_NAME,
                WikidataProperties.URL,
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
            property=WikidataProperties.COPYRIGHT_STATUS,
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
            "property": WikidataProperties.DESCRIBED_AT_URL,
            "value": f"https://www.flickr.com/photos/{user_id}/{photo_id}/",
        },
        {"property": WikidataProperties.OPERATOR, "entity_id": WikidataEntities.Flickr},
        {"property": WikidataProperties.URL, "value": jpeg_url},
    ]

    return {
        "mainsnak": _wikibase_entity_value(
            property=WikidataProperties.SOURCE_OF_FILE,
            wikidata_id=WikidataEntities.FileAvailableOnInternet,
        ),
        "qualifiers": _create_qualifiers(qualifier_values),
        "qualifiers-order": [
            WikidataProperties.DESCRIBED_AT_URL,
            WikidataProperties.OPERATOR,
            WikidataProperties.URL,
        ],
        "type": "statement",
    }
