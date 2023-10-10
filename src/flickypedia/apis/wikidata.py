import re

import httpx


def lookup_flickr_user_in_wikidata(*, id, name):
    """
    Return the Wikidata entity for a Flickr user, if it exists.

        >>> lookup_flickr_user_in_wikidata(id="1234567@N02", name="brandnew")
        None

        >>> lookup_flickr_user_in_wikidata(id="199246608@N02", name="ianemes")
        "Q5981474"

    Note that Wikidata entities are inconsistent about using the user ID
    (the numeric form) or the screen name  (which you see in URL slugs).
    For completeness of coverage, we search by both, if available.

    """
    # These two queries are looking for Wikidata entities which have
    # property P3267 with the given value (id and name).
    #
    # P3267 is the Wikidata property for Flickr user ID.
    #
    # See https://www.wikidata.org/wiki/Property:P3267 for an explanation
    # of how this property is used in Wikidata.
    #
    # I used https://stackoverflow.com/a/27212955/1558022 as the
    # starting point for these SPARQL queries.
    if name is None:
        query = """PREFIX wdt: <http://www.wikidata.org/prop/direct/>

        SELECT ?item WHERE {
          { ?item wdt:P3267 "%s" . }
        }""" % id
    else:
        query = """PREFIX wdt: <http://www.wikidata.org/prop/direct/>

        SELECT ?item WHERE {
          { ?item wdt:P3267 "%s" . }
          UNION
          { ?item wdt:P3267 "%s" . }
        }""" % (id, name)

    resp = httpx.get(
        "https://query.wikidata.org/sparql",
        params={"format": "json", "query": query}
    )

    resp.raise_for_status()

    # The returned result from the SPARQL query looks something like this:
    #
    #     {
    #       "head": {"vars": ["item", "itemLabel"]},
    #       "results": {
    #         "bindings": [
    #           {
    #             "item": {
    #               "type": "uri",
    #               "value": "http://www.wikidata.org/entity/Q5981474"
    #             }
    #           }
    #         ]
    #       }
    #     }
    #
    results = resp.json()['results']['bindings']

    from pprint import pprint; pprint(resp.json())

    # The list of matched entities is returned as a list.  In theory
    # we could get two or more entities back, in which case it's unclear
    # where we should map it -- in this case, log a warning and then give up.
    if len(results) > 1:
        print(f"Warning: ambiguous Wikidata entities found for Flickr user id={id} / name={name}")
        return

    # Look for something that looks like a single Wikidata entity URL
    # in the response.
    #
    # We're deliberately quite conservative here -- it's better to skip
    # linking an entity that exists that link an incorrect entity.
    try:
        matched_item = results[0]['item']

        # e.g. http://www.wikidata.org/entity/Q5981474
        uri_match = re.match(r'^http://www.wikidata.org/entity/(?P<wikidata_id>Q\d+)$', matched_item['value'])

        if matched_item['type'] == 'uri' and uri_match is not None:
            return uri_match.group('wikidata_id')

    except (IndexError, KeyError):
        pass
