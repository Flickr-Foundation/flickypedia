"""
This allows us to find Flickr photos from Wikitext alone.

This should help us to expose the ~1M photos which link to Flickr somewhere
in their Wikitext, but not in the structured data.

How it works:

*   We scan the Wikitext for anything that looks for a Flickr photo URL
*   Then we go and ask Flickr for each of those photos, and we compare it
    to the file on Commons
*   If they're a byte-for-byte match, we know we've found the original photo!

"""

import collections
from typing import TypedDict

import bs4
from flickr_url_parser import (
    parse_flickr_url,
    NotAFlickrUrl,
    UnrecognisedUrl,
)

from flickypedia.apis.structured_data import (
    AmbiguousStructuredData,
    find_flickr_urls_in_sdc,
)
from flickypedia.apis.structured_data.wikidata import WikidataProperties
from flickypedia.apis.wikimedia import WikimediaApi
from flickypedia.apis.flickr import FlickrPhotosApi, ResourceNotFound
from flickypedia.types.structured_data import ExistingClaims
from .comparisons import urls_have_same_contents


class FindResult(TypedDict):
    photo_id: str
    url: str | None


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
    wikimedia_api: WikimediaApi, flickr_api: FlickrPhotosApi, filename: str
) -> FindResult | None:
    """
    Given the name of a file on Wikimedia Commons, look for Flickr URLs
    in the Wikitext.  This looks for Flickr URLs in the Wikitext, then
    compares the file on Commons to the file on Flickr.

    Only matching files are returned.
    """
    wikitext = wikimedia_api.get_wikitext(filename)

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

        if len(anchor_tags) == 1:
            url = anchor_tags[0].attrs["href"]

            photo_id = get_flickr_photo_id_from_url(url)
            if photo_id is not None:
                return {"photo_id": photo_id, "url": url}

    # Now look for any links which are explicitly labelled as
    # "Source: <URL>" in the Wikitext.  For example:
    #
    #     Source: https://www.flickr.com/photos/justinaugust/3731022/
    #
    for anchor_tag in soup.find_all("a"):
        url = anchor_tag.attrs["href"]
        photo_id = get_flickr_photo_id_from_url(url)
        if photo_id is not None:
            if anchor_tag.parent.text == f"Source: {url}":
                return {"photo_id": photo_id, "url": url}

    # Then look for all the Flickr URLs, and try to find a URL which has
    # a JPEG that matches the file in Wikimedia Commons.
    #
    # We can look for the URLs in all the anchor tags.
    candidates = set(
        (a_tag.attrs["href"], get_flickr_photo_id_from_url(a_tag.attrs["href"]))
        for a_tag in soup.find_all("a")
    )

    for url, photo_id in sorted(candidates):
        if photo_id is None:
            continue

        try:
            photo = flickr_api.get_single_photo(photo_id=photo_id)
        except ResourceNotFound:
            continue

        try:
            original_size = [s for s in photo["sizes"] if s["label"] == "Original"][0]
        except IndexError:
            assert 0
            continue

        flickr_url = original_size["source"]
        wikimedia_url = wikimedia_api.get_image_url(filename)

        if urls_have_same_contents(flickr_url, wikimedia_url):
            return {"photo_id": photo_id, "url": url}

    return None


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
        candidates[photo_id].discard(None)
        return {"photo_id": photo_id, "url": candidates[photo_id].pop()}
