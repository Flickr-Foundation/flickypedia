"""
Look up Flickr users that have Wikidata entities.

When we're creating a P170 Creator statement, we link to the Flickr user
who posted the photo.  Normally, we create a couple of qualifiers that
include their Flickr username, their user ID, their profile, etc.

But if somebody has a Wikidata entity and that entity includes
their Flickr user ID, we'd rather link to that instead!  So this
module allows us to match Flickr users to Wikidata entities.

    >>> lookup_flickr_user_in_wikidata(user={'id': '57928590@N07'})
    'Q1201'

    >>> lookup_flickr_user_in_wikidata(user={'pathalias': 'dali_museum'})
    'Q674427'

See discussion here:
https://commons.wikimedia.org/wiki/Commons_talk:Flickypedia/Data_Modeling#Creator

============
How it works
============

There are only ~2600 Flickr users who have Wikidata entities -- the vast
majority won't.

We could query the Wikidata SPARQL endpoint every time we want to look up
a Flickr user, but that introduces latency for a query that will mostly
come up empty.

Instead, we do a one-off query for _all_ the Wikidata entities that
have the Flickr user ID property.  This can be cached in-memory (it's
small, only ~86KB of JSON) and then looked up for the lifetime of
the program.

"""

import functools
import re
from typing import TypedDict

from flickypedia.types.flickr import User as FlickrUser
import httpx

from flickypedia.apis.structured_data.wikidata import WikidataProperties


def lookup_flickr_user_in_wikidata(user: FlickrUser) -> str | None:
    """
    If this Flickr user is linked to a Wikidata entity, return the
    Q-ID of that Wikidata entity.

    Otherwise, return None.
    """
    lookup = find_wikidata_entities_with_flickr_ids()

    try:
        return lookup["by_user_id"][user["id"]]
    except KeyError:
        pass

    if user["path_alias"] is not None:
        try:
            return lookup["by_pathalias"][user["path_alias"]]
        except KeyError:
            pass

    return None


def is_flickr_user_id(s: str) -> bool:
    """
    Returns True if a string looks like a Flickr user ID.

        >>> is_flickr_user_id("192202757@N07")
        True

        >>> is_flickr_user_id("janesmith")
        False

    """
    return re.match(r"^[0-9]{5,11}@N[0-9]{2}$", s) is not None


class WikidataEntityLookup(TypedDict):
    by_user_id: dict[str, str]
    by_pathalias: dict[str, str]


@functools.cache
def find_wikidata_entities_with_flickr_ids() -> WikidataEntityLookup:
    """
    Creates a dictionary that maps Flickr user IDs to Wikidata entity IDs.
    """
    result: WikidataEntityLookup = {
        "by_user_id": {},
        "by_pathalias": {},
    }

    # Run a SPARQL query to find all the Wikidata entities that have
    # the Flickr photo ID property.
    #
    # This is based on https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/queries/examples#All_items_with_a_property
    resp = httpx.get(
        "https://query.wikidata.org/sparql",
        params={
            "format": "json",
            "query": """
                SELECT ?item ?value
                WHERE { ?item wdt:%s ?value }
                LIMIT 5000
            """
            % WikidataProperties.FlickrUserId,
        },
    )

    for entity in resp.json()["results"]["bindings"]:
        # Each entity will be a dict something of the form:
        #
        #     {
        #       'item': {
        #         'type': 'uri',
        #         'value': 'http://www.wikidata.org/entity/Q1201'
        #       },
        #       'value': {'type': 'literal', 'value': '57928590@N07'}
        #     }
        #
        if (
            entity["item"]["type"] != "uri"
            or not entity["item"]["value"].startswith("http://www.wikidata.org/entity/")
            or entity["value"]["type"] != "literal"
        ):
            continue  # pragma: no cover

        wikidata_entity_id = entity["item"]["value"].replace(
            "http://www.wikidata.org/entity/", ""
        )
        wikidata_text = entity["value"]["value"]

        if is_flickr_user_id(wikidata_text):
            result["by_user_id"][wikidata_text] = wikidata_entity_id
        else:
            result["by_pathalias"][wikidata_text] = wikidata_entity_id

    return result
