"""
Functions for creating structured data entities for use with the
Wikimedia APIs.

The goal of this file is to create some helpers and templates to reduce
the amount of repetition required when creating these entities.
"""

from flickypedia.apis.wikidata import lookup_flickr_user_in_wikidata


class WikidataProperties:
    """
    Named constants for Wikidata property names.
    """

    # https://www.wikidata.org/wiki/Property:P170
    CREATOR = "P170"


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
            "mainsnak": {
                "snaktype": "value",
                "property": WikidataProperties.CREATOR,
                "datavalue": {
                    "type": "wikibase-entityid",
                    "value": {"id": wikidata_id},
                },
            },
            "type": "statement",
        }
