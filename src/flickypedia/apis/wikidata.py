import functools

import httpx

from .structured_data.wikidata import WikidataProperties


@functools.lru_cache
def get_flickr_user_id(entity_id: str) -> str | None:
    """
    Look up the Flickr User ID for a Wikidata entity.

    This may return None if this Wikidata entity isn't associated with
    a Flickr user.
    """
    resp = httpx.get(
        f"https://www.wikidata.org/w/rest.php/wikibase/v0/entities/items/{entity_id}"
    )

    # The rough structure of the response that we're interested in is:
    #
    #     {
    #       "statements": {
    #         "P3267": [
    #           {"value": {"type": "value", "content": "65001151@N03"}}
    #         ]
    #       }
    #     }
    #
    try:
        resp.raise_for_status()
        flickr_user_id = resp.json()["statements"][WikidataProperties.FlickrUserId][0]
        return flickr_user_id["value"]["content"]  # type: ignore
    except Exception:
        return None
