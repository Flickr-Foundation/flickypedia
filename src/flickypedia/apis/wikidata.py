import re

import httpx


class WikidataProperties:
    """
    Named constants for Wikidata property names.
    """

    # To see documentation for a particular property, go to
    # https://www.wikidata.org/wiki/Property:<PROPERTY_ID>
    #
    # e.g. https://www.wikidata.org/wiki/Property:P2093
    Operator = "P137"
    Creator = "P170"
    DescribedAtUrl = "P973"
    AuthorName = "P2093"
    FlickrUserId = "P3267"
    Url = "P2699"
    SourceOfFile = "P7482"
    CopyrightLicense = "P275"
    CopyrightStatus = "P6216"


class WikidataEntities:
    """
    Named constants for certain Wikidata entities.
    """

    # To see documentation for a particular property, go to
    # https://www.wikidata.org/wiki/<ENTITY_ID>
    #
    # e.g. https://www.wikidata.org/wiki/Q103204
    Copyrighted = "Q50423863"
    FileAvailableOnInternet = "Q74228490"
    Flickr = "Q103204"

    Licenses = {
        "cc-by-2.0": "Q19125117",
        "cc-by-nc-2.0": "Q44128984",
        "cc-by-nc-nd-2.0": "Q47008927",
        "cc-by-nc-sa-2.0": "Q28050835",
        "cc-by-nd-2.0": "Q35254645",
        "cc-by-sa-2.0": "Q19068220",
        "cc-0-1.0": "Q6938433",
        # TODO: Flickr has a statement "US Government Work" which we
        # might need to map here; if so, consider this entity:
        # https://www.wikidata.org/wiki/Q60671452
    }


def lookup_flickr_user_in_wikidata(*, id, username):
    """
    Return the Wikidata entity for a Flickr user, if it exists.

        >>> lookup_flickr_user_in_wikidata(id="1234567@N02", username="brandnew")
        None

        >>> lookup_flickr_user_in_wikidata(id="199246608@N02", username="ianemes")
        "Q5981474"

    Note that Wikidata entities are inconsistent about using the user ID
    (the numeric form) or the screen name  (which you see in URL slugs).
    For completeness of coverage, we search by both, if available.

    """
    # These two queries are looking for Wikidata entities which have
    # property P3267 (Flickr user ID) with the given value (id and name).
    #
    # I used https://stackoverflow.com/a/27212955/1558022 as the
    # starting point for these SPARQL queries.
    if username is None:
        query = """PREFIX wdt: <http://www.wikidata.org/prop/direct/>

        SELECT ?item WHERE {
          { ?item wdt:%s "%s" . }
        }""" % (
            WikidataProperties.FlickrUserId,
            id,
        )
    else:
        query = """PREFIX wdt: <http://www.wikidata.org/prop/direct/>

        SELECT ?item WHERE {
          { ?item wdt:%s "%s" . }
          UNION
          { ?item wdt:%s "%s" . }
        }""" % (
            WikidataProperties.FlickrUserId,
            id,
            WikidataProperties.FlickrUserId,
            username,
        )

    resp = httpx.get(
        "https://query.wikidata.org/sparql", params={"format": "json", "query": query}
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
    results = resp.json()["results"]["bindings"]

    # The list of matched entities is returned as a list.  In theory
    # we could get two or more entities back, in which case it's unclear
    # where we should map it -- in this case, log a warning and then give up.
    if len(results) > 1:
        print(
            f"Warning: ambiguous Wikidata entities found for Flickr user id={id} / username={username}"
        )
        return

    # Look for something that looks like a single Wikidata entity URL
    # in the response.
    #
    # We're deliberately quite conservative here -- it's better to skip
    # linking an entity that exists that link an incorrect entity.
    try:
        matched_item = results[0]["item"]

        # e.g. http://www.wikidata.org/entity/Q5981474
        uri_match = re.match(
            r"^http://www.wikidata.org/entity/(?P<wikidata_id>Q\d+)$",
            matched_item["value"],
        )

        if matched_item["type"] == "uri" and uri_match is not None:
            return uri_match.group("wikidata_id")

    except (IndexError, KeyError):
        pass
