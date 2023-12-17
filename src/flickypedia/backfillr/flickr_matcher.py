"""
Match existing Wikimedia Commons files to photos on Flickr.

This looks for information that points to the original Flickr photo
in the structured data and Wikitext.

We prefer looking in the structured data over Wikitext, because we have
to rely on heuristics rather than explicit machine-readable data.
"""

import collections
from typing import TypedDict

import bs4
from flickr_url_parser import (
    parse_flickr_url,
    NotAFlickrUrl,
    ParseResult,
    UnrecognisedUrl,
)

from flickypedia.apis.structured_data.wikidata import (
    WikidataEntities,
    WikidataProperties,
    to_wikidata_entity_value,
)
from flickypedia.apis.wikimedia import WikimediaApi
from flickypedia.types.structured_data import ExistingClaims, ExistingStatement, Snak


def pick_best_url(urls: set[str | None]) -> str:
    """
    Given a list of URLs which all represent the same Flickr photo,
    pick the "best" one.
    """
    string_urls = {u for u in urls if u is not None}
    assert len(string_urls) > 0

    # We sort alphabetically and pick the last one, which prioritises
    # URLs from www.flickr.com over the various staticflickr.com subdomains.
    return sorted(string_urls)[-1]


class FindResult(TypedDict):
    photo_id: str
    url: str | None


def is_flickr_homepage(url: str) -> bool:
    """
    Given a URL, check if it's the Flickr.com homepage.
    """
    try:
        parsed_url = parse_flickr_url(url)
    except (NotAFlickrUrl, UnrecognisedUrl):
        return False
    else:
        return parsed_url["type"] == "homepage"


def get_flickr_photo_id_from_url(url: str) -> str | None:
    """
    Given a URL, return the photo ID (if it points to a Flickr photo)
    or None otherwise.
    """
    try:
        parsed_url = parse_flickr_url(url)
    except (NotAFlickrUrl, UnrecognisedUrl):
        return None
    else:
        if parsed_url["type"] == "single_photo":
            return parsed_url["photo_id"]
        else:
            return None


def find_flickr_photo_id_from_source_field(row_element: bs4.element.Tag) -> FindResult | None:
    """
    Given the <td> element for the "Source" field in the "Information" table,
    try to work out which Flickr photo this points to.

    The goal is not to provide a complete matching of all Flickr URLs
    in this field, but to handle any "obvious" patterns that a human
    would reasonably trust to be a link to the source photo.
    """
    urls = [
        a_tag.attrs['href']
        for a_tag in row_element.find_all("a")
    ]

    # If there's a single URL that points to a Flickr photo, we can assume
    # that's the original Flickr photo. e.g.
    #
    #     Source: [link to Flickr photo]
    #
    if len(urls) == 1:
        single_url = urls[0]

        photo_id = get_flickr_photo_id_from_url(single_url)
        if photo_id is not None:
            return {"photo_id": photo_id, "url": single_url}

    # If there are two URLs and the first one points to the Wikipedia page
    # for Flickr and the second to the Flickr photo, we can assume that's
    # the original Flickr photo. e.g.
    #
    #     Source: This image was originally posted to [Flickr] as [photo]
    #
    elif len(urls) == 2 and urls[0] == "https://en.wikipedia.org/wiki/Flickr":
        single_url = urls[1]

        photo_id = get_flickr_photo_id_from_url(single_url)
        if photo_id is not None:
            return {"photo_id": photo_id, "url": single_url}

    # If there are two URLs and the first one points to the Flickr homepage
    # and the second to a Flickr photo, we can assume that's the original
    # Flickr photo. e.g.
    #
    #      [Flickr.com]: [link to individual photo]
    #
    elif len(urls) == 2:
        try:
            parsed_url0 = parse_flickr_url(urls[0])
            parsed_url1 = parse_flickr_url(urls[1])
        except (NotAFlickrUrl, UnrecognisedUrl):
            assert 0
            pass
        else:
            if (
                parsed_url0["type"] == "homepage"
                and parsed_url1["type"] == "single_photo"
            ):
                return {"photo_id": parsed_url1["photo_id"], "url": urls[1]}
            else:
                assert 0



def find_flickr_photo_id_from_wikitext(
    wikitext: str, filename: str
) -> FindResult | None:
    """
    Given the name of a file on Wikimedia Commons, look for Flickr URLs
    in the Wikitext.  This looks for Flickr URLs in the Wikitext, then
    compares the file on Commons to the file on Flickr.

    Only matching files are returned.
    """
    soup = bs4.BeautifulSoup(wikitext, "html.parser")

    # Look for an Information table in the Wikitext.
    #
    # This may link to the Flickr photo in the "Source" field.  Here's
    # an example of what this table should look like:
    #
    #     <table class="fileinfotpl-type-information">
    #       …
    #       <tr>
    #         <td id="fileinfotpl_src" class="fileinfo-paramfield" lang="en">Source</td>
    #         <td>
    #           <a rel="nofollow" href="http://www.flickr.com/photos/stewart/253009/">Flickr</a>
    #         </td>
    #       </tr>
    #
    information_source_elems = soup.find_all("td", attrs={"id": "fileinfotpl_src"})

    if len(information_source_elems) == 1:
        information_source_td = information_source_elems[0]

        row = information_source_td.parent

        find_result = find_flickr_photo_id_from_source_field(row)
        if find_result is not None:
            return find_result

    # Now look for any links which are explicitly labelled as
    # "Source: <URL>" in the Wikitext.  For example:
    #
    #     <li>Source: https://www.flickr.com/photos/justinaugust/3731022/</li>
    #     <p>Source: https://www.flickr.com/photos/metalphoenix/3874334/\n</p>
    #
    for anchor_tag in soup.find_all("a"):
        url = anchor_tag.attrs["href"]
        photo_id = get_flickr_photo_id_from_url(url)
        if photo_id is not None:
            if anchor_tag.parent.text.strip() in {
                f"Source: {url}",
                "Source: Flickr",
                "Source: Flickr.",
            }:
                return {"photo_id": photo_id, "url": url}

    return None


def get_single_qualifier(
    statement: ExistingStatement, *, property_id: str
) -> Snak | None:
    """
    A statement can have qualifiers:

        statement: {
            qualifiers: Qualifiers
            ...
        }

    In most cases, there's exactly one Snak per property ID, e.g.

        statement: {
            qualifiers: {
                P123: [Snak],
                P456: [Snak],
            }
        }

    This function looks for exactly one Snak in a property, and returns
    it if found.

    If there are no Snaks (this property isn't used as a qualifier) or
    there are multiple Snaks for a property, it returns ``None``.
    """
    qualifiers = statement.get("qualifiers", {})

    snak_list = qualifiers.get(property_id, [])

    if len(snak_list) == 0:
        return None

    if len(snak_list) != 1:
        raise AmbiguousStructuredData(
            f"Unexpected multiple qualifiers in {statement['id']}"
        )

    return snak_list[0]


class AmbiguousStructuredData(Exception):
    pass


def find_flickr_urls_in_sdc(sdc: ExistingClaims) -> list[tuple[str, ParseResult]]:
    """
    Return a list of Flickr URLs which were found in the SDC.

    These are guaranteed to be parseable using flickr-url-parser.
    """
    result: list[tuple[str, ParseResult]] = []

    # Look for URLs in the "Source" field, which might point to
    # a Flickr photo.
    for statement in sdc.get(WikidataProperties.SourceOfFile, []):
        # First check if the Operator is "Flickr".  If it's not, this
        # isn't a Flickr source and we can skip it.
        operator = get_single_qualifier(
            statement, property_id=WikidataProperties.Operator
        )

        flickr = to_wikidata_entity_value(entity_id=WikidataEntities.Flickr)

        if operator is not None and operator["datavalue"] != flickr:
            continue

        # Now look at the "URL" and "Published at" qualifiers.  Either of
        # them could contain a Flickr URL.
        url = get_single_qualifier(statement, property_id=WikidataProperties.Url)
        published_at = get_single_qualifier(
            statement, property_id=WikidataProperties.DescribedAtUrl
        )

        for u in (url, published_at):
            if u is None:
                continue

            if u["datavalue"]["type"] != "string":
                continue

            value = u["datavalue"]["value"]

            try:
                parsed_url = parse_flickr_url(value)
            except (UnrecognisedUrl, NotAFlickrUrl):
                pass
            else:
                result.append((value, parsed_url))

    return result


def find_flickr_photo_id_from_sdc(sdc: ExistingClaims) -> FindResult | None:
    """
    Given the structured data for a file on Wikimedia Commons, guess
    what Flickr photo ID this is associated with (if any).

    Note: there are a bunch of `assert 0`'s littered through this code,
    which are branches I haven't tested because I haven't encountered
    them in practice yet.  If you hit one of these in practice, use it
    as an example to write a test!
    """
    candidates: dict[str, set[str | None]] = collections.defaultdict(set)

    # Look for Flickr URLs in the "Source" field.
    for url, parsed_url in find_flickr_urls_in_sdc(sdc):
        if parsed_url["type"] == "single_photo":
            candidates[parsed_url["photo_id"]].add(url)
        else:
            raise AmbiguousStructuredData(f"Ambiguous Flickr URL: {url}")

    # Look for a photo ID in the "Flickr Photo ID" field.
    for statement in sdc.get(WikidataProperties.FlickrPhotoId, []):
        if statement["mainsnak"]["datavalue"]["type"] == "string":
            photo_id = statement["mainsnak"]["datavalue"]["value"]
            candidates[photo_id].add(None)

    if len(candidates) > 1:
        raise ValueError(f"Ambiguous set of Flickr photo IDs: {candidates}")

    if not candidates:
        return None

    photo_id = list(candidates.keys())[0]

    if candidates[photo_id] == {None}:
        return {"photo_id": photo_id, "url": None}
    else:
        return {"photo_id": photo_id, "url": pick_best_url(candidates[photo_id])}


def find_flickr_photo(
    wikimedia_api: WikimediaApi,
    existing_sdc: ExistingClaims,
    filename: str,
) -> FindResult | None:
    find_result = find_flickr_photo_id_from_sdc(existing_sdc)

    if find_result is not None:
        return find_result

    wikitext = wikimedia_api.get_wikitext(filename)

    find_result = find_flickr_photo_id_from_wikitext(
        wikitext, filename=f"File:{filename}"
    )

    return find_result
