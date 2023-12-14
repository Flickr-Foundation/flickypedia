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

from flickr_url_parser import (
    find_flickr_urls_in_text,
    parse_flickr_url,
    NotAFlickrUrl,
    UnrecognisedUrl,
)

from flickypedia.apis.wikimedia import WikimediaApi
from flickypedia.apis.flickr import FlickrPhotosApi
from .comparisons import urls_have_same_contents


def find_flickr_photo_id_from_wikitext(
    wikimedia_api: WikimediaApi, flickr_api: FlickrPhotosApi, filename: str
) -> str | None:
    """
    Given the name of a file on Wikimedia Commons, look for Flickr URLs
    in the Wikitext.  This looks for Flickr URLs in the Wikitext, then
    compares the file on Commons to the file on Flickr.

    Only matching files are returned.
    """
    wikitext = wikimedia_api.get_wikitext(filename)

    candidates = set()

    for url in find_flickr_urls_in_text(wikitext):
        try:
            parsed_url = parse_flickr_url(url)
        except (NotAFlickrUrl, UnrecognisedUrl):
            continue

        if parsed_url["type"] == "single_photo":
            candidates.add(parsed_url["photo_id"])

    for photo_id in sorted(candidates):
        photo = flickr_api.get_single_photo(photo_id=photo_id)

        try:
            original_size = [s for s in photo["sizes"] if s["label"] == "Original"][0]
        except IndexError:
            return None

        flickr_url = original_size["source"]
        wikimedia_url = wikimedia_api.get_image_url(filename)

        if urls_have_same_contents(flickr_url, wikimedia_url):
            return photo_id
        else:
            print(photo_id, "files don't match!")

    return None
