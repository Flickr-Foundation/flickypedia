import pytest

from flickypedia.apis.wikimedia import WikimediaApi
from flickypedia.apis.flickr import FlickrPhotosApi
from flickypedia.backfillr.flickr_matcher import (
    find_flickr_photo_id_from_wikitext,
    FindResult,
)


@pytest.mark.parametrize(
    ["filename", "photo_id"],
    [
        ("Example.jpg", None),
        #
        # This has a Flickr photo URL in the Wikitext
        (
            "A breezy day in Venice (1890s), by Ettore Tito.png",
            {
                "photo_id": "49800608076",
                "url": "https://www.flickr.com/photos/gandalfsgallery/49800608076/in/photostream/",
            },
        ),
        #
        # This has a Flickr URL in the Wikitext, but it links to
        # the author's profile rather than the photo
        ("The main Flickr photo storage server.jpg", None),
        #
        # This has a Flickr photo ID in the "Source" row of the
        # "Information" table, so we can match it even though the original
        # photo can no longer be downloaded from Flickr.
        (
            "EI-DYY (15602283025).jpg",
            {
                "photo_id": "15602283025",
                "url": "https://www.flickr.com/photos/golfking1/15602283025/",
            },
        ),
        #
        # These have multiple Flickr photo URLs in the Wikitext, and only
        # one of them points to the original photo.
        (
            "Intel 8742 153056995.jpg",
            {
                "photo_id": "153056995",
                "url": "https://www.flickr.com/photos/biwook/153056995/",
            },
        ),
        (
            "Taking photo.jpg",
            {
                "photo_id": "9078889",
                "url": "https://www.flickr.com/photos/48889110751@N01/9078889",
            },
        ),
        #
        # This has Flickr photo URLs in the Wikitext, but they point to
        # different photos.
        ("Graffiti Rosario - Darío y Maxi.jpg", None),
        #
        # This has a Flickr photo ID in the "Source" row of the
        # "Information" table, so we can match it even though the original
        # photo has been deleted from Flickr.
        (
            "Stewart-White line in the road spraying machine.jpg",
            {
                "photo_id": "253009",
                "url": "http://www.flickr.com/photos/stewart/253009/",
            },
        ),
        #
        # This has a Flickr URL in the Wikitext, but the original photo
        # has been deleted and there's nothing to tell us this URL is
        # significant above others.
        ("Stewart-Baseball cropped.jpg", None),
        #
        # This has a Flickr URL in the Wikitext, and it points to a
        # file which is byte-for-byte identical to the file on Commons.
        (
            "Dustpuppy-Autobahn.jpg",
            {
                "photo_id": "1574718",
                "url": "https://live.staticflickr.com/2/1574718_b83292bc7e_o.jpg",
            },
        ),
        #
        # This has a Flickr URL in the Wikitext, which is clearly
        # identified as the Source in a paragraph that labels it as such.
        (
            "Dan Potthast.jpg",
            {
                "photo_id": "3731022",
                "url": "https://www.flickr.com/photos/justinaugust/3731022/",
            },
        ),
    ],
)
def test_find_flickr_photo_id_from_wikitext(
    wikimedia_api: WikimediaApi,
    flickr_api: FlickrPhotosApi,
    filename: str,
    photo_id: FindResult | None,
) -> None:
    assert photo_id == find_flickr_photo_id_from_wikitext(
        wikimedia_api, flickr_api, filename=f"File:{filename}"
    )
