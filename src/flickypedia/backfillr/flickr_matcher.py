import httpx

from flickypedia.apis.wikimedia import WikimediaApi
from flickypedia.apis.flickr import FlickrPhotosApi
from flickr_url_parser import (
    find_flickr_urls_in_text,
    parse_flickr_url,
    NotAFlickrUrl,
    UnrecognisedUrl,
)


def compare_urls(url1, url2):
    try:
        response1 = httpx.get(url1)
        response1.raise_for_status()
        content1 = response1.text

        response2 = httpx.get(url2)
        response2.raise_for_status()
        content2 = response2.text

        return content1 == content2

    except Exception:
        return False


def find_flickr_photo_id_for_file(
    wikimedia_api: WikimediaApi, flickr_api: FlickrPhotosApi, filename: str
) -> str | None:
    wikitext = wikimedia_api.get_wikitext(filename)

    candidates = set()

    for url in find_flickr_urls_in_text(wikitext):
        try:
            parsed_url = parse_flickr_url(url)
        except (NotAFlickrUrl, UnrecognisedUrl):
            continue

        if parsed_url["type"] == "single_photo":
            candidates.add(parsed_url["photo_id"])

    if len(candidates) != 1:
        return None

    photo_id = candidates.pop()
    photo = flickr_api.get_single_photo(photo_id=photo_id)

    try:
        original_size = [s for s in photo["sizes"] if s["label"] == "Original"][0]
    except IndexError:
        return None

    flickr_url = original_size["source"]
    wikimedia_url = wikimedia_api.get_image_url(filename)

    return compare_urls(flickr_url, wikimedia_url)
