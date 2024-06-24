from ..wikidata_properties import WikidataProperties
from ..types import NewStatement, to_wikidata_string_value


def create_flickr_photo_id_statement(photo_id: str) -> NewStatement:
    """
    Creates a Flickr Photo ID statement for a Flickr photo.

    This is a main statement rather than a qualifier on another statement;
    this is to match the convention of e.g. YouTube video ID.
    """
    return {
        "mainsnak": {
            "datavalue": to_wikidata_string_value(value=photo_id),
            "property": WikidataProperties.FlickrPhotoId,
            "snaktype": "value",
        },
        "type": "statement",
    }
