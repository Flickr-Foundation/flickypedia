"""
Create a statement for BHL Page ID.

Here BHL = Biodiversity Heritage Library
https://www.flickr.com/photos/biodivlibrary/
"""

from flickr_photos_api import MachineTags

from ..types import NewStatement, to_wikidata_string_value
from ..wikidata_properties import WikidataProperties


def guess_bhl_page_id(*, photo_id: str, machine_tags: MachineTags) -> str | None:
    """
    Given the metadata from the original Flickr photo, work out what
    the BHL Page ID for this photo is (if any).

    == How it works ==

    We look for a machine tag with the `bhl:page` namespace.

    BHL photos usually include a link to the page, but we can't trust
    it to point to the original photo.  Sometimes these are ambiguous --
    we don't trust these links, so we don't look at them.
    """
    # Most BHL photos have a machine tag of the form:
    #
    #     bhl:page=33665643
    #
    # Look for any tags which match this pattern.
    candidate_page_ids = set(machine_tags.get("bhl", {}).get("page", []))

    # In general we expect that this should be an unambiguous list --
    # however, we double check to be sure!
    if not candidate_page_ids:
        print(f"Warning: no BHL page ID on {photo_id}")
        return None
    elif len(candidate_page_ids) == 1:
        return candidate_page_ids.pop()
    else:
        print(f"Warning: ambiguous BHL page ID on {photo_id} ({candidate_page_ids})")
        return None


def create_bhl_page_id_statement(
    *, photo_id: str, machine_tags: MachineTags
) -> NewStatement | None:
    """
    Creates a BHL Photo ID statement for a Flickr photo.
    """
    bhl_page_id = guess_bhl_page_id(photo_id=photo_id, machine_tags=machine_tags)

    if bhl_page_id is not None:
        return {
            "mainsnak": {
                "datavalue": to_wikidata_string_value(value=bhl_page_id),
                "property": WikidataProperties.BhlPageId,
                "snaktype": "value",
            },
            "type": "statement",
        }
    else:
        return None
