"""
Match existing Wikimedia Commons files to photos on Flickr.

This looks for information that points to the original Flickr photo
in the structured data and Wikitext.

We prefer looking in the structured data over Wikitext, because we have
to rely on heuristics rather than explicit machine-readable data.
"""

import collections
import typing

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


class FindResult(typing.TypedDict):
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

        # Now look for a single <a> tag inside the <td>.  We look at
        # the href attribute, because the text is sometimes a human-readable
        # label rather than the URL.
        anchor_tags = row.find_all("a")
        urls = [a_tag.attrs.get("href") for a_tag in anchor_tags]

        if len(urls) == 1:
            url = urls[0]

            photo_id = get_flickr_photo_id_from_url(url)
            if photo_id is not None:
                return {"photo_id": photo_id, "url": url}

        # Now look for two <a> tags; a common pattern is for somebody to
        # link to both Flickr.com and the individual photo page.
        #
        # For example:
        #
        #     <td>
        #       <a href="https://www.flickr.com/">Flickr.com</a> -
        #       <a href="https://www.flickr.com/photos/51035573370@N01/869031">
        #         image description page
        #       </a>
        #     </td>
        #
        if len(anchor_tags) == 2 and is_flickr_homepage(urls[0]):
            url = urls[1]

            photo_id = get_flickr_photo_id_from_url(url)
            if photo_id is not None:
                return {"photo_id": photo_id, "url": url}

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
            if anchor_tag.parent.text.strip() in {f"Source: {url}", "Source: Flickr"}:
                return {"photo_id": photo_id, "url": url}

    return None


def get_qualifiers(statement: ExistingStatement, *, property_id: str) -> list[Snak]:
    """
    A statement can have qualifiers:

        statement: {
            qualifiers: Qualifiers
            ...
        }

    This function returns all the qualifiers for a property ID.
    """
    qualifiers = statement.get("qualifiers", {})

    snak_list = qualifiers.get(property_id, [])

    return snak_list


def get_single_qualifier(
    statement: ExistingStatement, *, property_id: str
) -> Snak | None:
    """
    A statement can have qualifiers:

        statement: {
            qualifiers: Qualifiers
            ...
        }

    This function returns all the qualifiers for a property ID.

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
    qualifiers = get_qualifiers(statement, property_id=property_id)

    if len(qualifiers) == 0:
        return None

    if len(qualifiers) != 1:
        raise AmbiguousStructuredData(
            f"Unexpected multiple qualifiers for {property_id} in {statement['id']}"
        )

    return qualifiers[0]


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

        if operator is not None and operator.get("datavalue") != flickr:
            continue

        # Now look at the "URL" and "Published at" qualifiers.  Either of
        # them could contain a Flickr URL.
        urls = get_qualifiers(statement, property_id=WikidataProperties.Url)
        published_at = get_qualifiers(
            statement, property_id=WikidataProperties.DescribedAtUrl
        )

        for u in urls + published_at:
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
