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


def _link_to_wikibase_entity(*, property, wikidata_id):
    return {
        "mainsnak": {
            "snaktype": "value",
            "property": property,
            "datavalue": {
                "type": "wikibase-entityid",
                "value": {"id": wikidata_id},
            },
        },
        "type": "statement",
    }


def create_flickr_creator_data(user_id, username, realname):
    """
    Create a structured data claim for a user on Flickr.

    This is either:

    *   A link to the corresponding Wikidata entity, or
    *   A collection of values that link to their profile page

    """
    wikidata_id = lookup_flickr_user_in_wikidata(id=user_id, username=username)

    if wikidata_id is not None:
        return _link_to_wikibase_entity(
            property=WikidataProperties.CREATOR, wikidata_id=wikidata_id
        )
    else:
        qualifier_values = [
            (WikidataProperties.AUTHOR_NAME, realname or username),
            (WikidataProperties.URL, f"https://www.flickr.com/photos/{user_id}/"),
            (WikidataProperties.FLICKR_USER_ID, user_id),
        ]

        qualifiers = {
            property_id: [
                {
                    "datavalue": {"type": "string", "value": value},
                    "property": property_id,
                    "snaktype": "value",
                }
            ]
            for property_id, value in qualifier_values
        }

        return {
            "mainsnak": {
                "snaktype": "somevalue",
                "property": WikidataProperties.CREATOR,
            },
            "qualifiers": qualifiers,
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

    return _link_to_wikibase_entity(
        property=WikidataProperties.COPYRIGHT_STATUS,
        wikidata_id=WikidataEntities.Copyrighted,
    )
