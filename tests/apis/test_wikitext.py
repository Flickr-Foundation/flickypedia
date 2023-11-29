import datetime

from flickr_photos_api import SinglePhoto

from flickypedia.apis.wikitext import create_wikitext


def test_create_wikitext_for_photo() -> None:
    photo: SinglePhoto = {
        "id": "32812033543",
        "title": "Puppy Kisses",
        "owner": {
            "id": "30884892@N08",
            "username": "U.S. Coast Guard",
            "realname": "Coast Guard",
            "path_alias": "coast_guard",
            "photos_url": "https://www.flickr.com/photos/coast_guard/",
            "profile_url": "https://www.flickr.com/people/coast_guard/",
        },
        "date_posted": datetime.datetime(2017, 3, 24, 17, 27, 52),
        "date_taken": {
            "value": datetime.datetime(2017, 2, 17),
            "granularity": "second",
            "unknown": False,
        },
        "safety_level": "safe",
        "license": {
            "id": "usgov",
            "label": "United States Government Work",
            "url": "http://www.usa.gov/copyright.shtml",
        },
        "url": "https://www.flickr.com/photos/coast_guard/32812033543/",
        "description": None,
        "original_format": "jpg",
        "location": None,
        "sizes": [],
        "tags": [],
    }

    actual = create_wikitext(photo=photo, wikimedia_user_name="Example")
    expected = """=={{int:filedesc}}==
{{Information}}

=={{int:license-header}}==
{{usgov}}

{{Uploaded with Flickypedia|user=Example
|date=2023-11-29
|flickrUser=Coast Guard
|flickrUserUrl=https://www.flickr.com/people/coast_guard/
|flickrPhotoUrl=https://www.flickr.com/photos/coast_guard/32812033543/
}}"""

    assert actual == expected
