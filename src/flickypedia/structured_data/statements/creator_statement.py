from flickr_photos_api import User as FlickrUser

from ..types import NewStatement, QualifierValues, create_qualifiers
from ..wikidata_properties import WikidataProperties


def create_flickr_creator_statement(user: FlickrUser) -> NewStatement:
    """
    Create a structured data statement for a user on Flickr.

    This is either:

    *   A link to the corresponding Wikidata entity, or
    *   A collection of values that link to their profile page

    """
    qualifier_values: list[QualifierValues] = [
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
