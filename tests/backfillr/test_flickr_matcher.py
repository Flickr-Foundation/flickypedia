import pytest

from flickypedia.apis.wikimedia import WikimediaApi
from flickypedia.apis.flickr import FlickrPhotosApi
from flickypedia.backfillr.flickr_matcher import find_flickr_photo_id_from_wikitext


@pytest.mark.parametrize(
    ["filename", "photo_id"],
    [
        ("Example.jpg", None),
        #
        # This has a Flickr photo URL in the Wikitext
        ("A breezy day in Venice (1890s), by Ettore Tito.png", "49800608076"),
        #
        # This has a Flickr URL in the Wikitext, but it links to
        # the author's profile rather than the photo
        ("The main Flickr photo storage server.jpg", None),
        #
        # This has a Flickr photo URL in the Wikitext, but we can't retrieve
        # the original URL from Flickr because the user disabled downloads
        # sometime after the initial copy to Commons.
        ("EI-DYY (15602283025).jpg", None),
        #
        # These have multiple Flickr photo URLs in the Wikitext, and only
        # one of them points to the original photo.
        ("Intel 8742 153056995.jpg", "153056995"),
        ("Taking photo.jpg", "9078889"),
        #
        # This has Flickr photo URLs in the Wikitext, but they point to
        # different photos.
        ("Graffiti Rosario - Darío y Maxi.jpg", None),
    ],
)
def test_find_flickr_photo_id_from_wikitext(
    wikimedia_api: WikimediaApi,
    flickr_api: FlickrPhotosApi,
    filename: str,
    photo_id: str | None,
) -> None:
    assert photo_id == find_flickr_photo_id_from_wikitext(
        wikimedia_api, flickr_api, filename=f"File:{filename}"
    )
