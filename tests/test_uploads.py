import datetime

from flask import Flask

from flickypedia.apis.wikimedia import WikimediaApi
from flickypedia.duplicates import find_duplicates
from flickypedia.uploads import upload_single_image


def test_upload_single_image(app: Flask, wikimedia_api: WikimediaApi) -> None:
    before_duplicates = find_duplicates(flickr_photo_ids=["53268016608"])
    assert before_duplicates == {}

    upload_single_image(
        wikimedia_api,
        photo_id="53268016608",
        photo_url="https://www.flickr.com/photos/199246608@N02/53268016608",
        user={
            "id": "199246608@N02",
            "username": "cefarrjf87",
            "realname": "Alex Chan",
            "photos_url": "https://www.flickr.com/photos/199246608@N02/",
            "profile_url": "https://www.flickr.com/people/199246608@N02/",
        },
        filename="Thameslink Class 700 in Pride livery.jpg",
        file_caption_language="en",
        file_caption="A Thameslink Class 700 train in the rainbow Pride livery, taken at night",
        date_taken={
            "value": datetime.datetime(2023, 9, 12, 19, 54, 32),
            "granularity": "second",
            "unknown": False,
        },
        date_posted=datetime.datetime.fromtimestamp(1697645772),
        license_id="cc-by-2.0",
        original_url="https://live.staticflickr.com/65535/53268016608_5b890124fd_o_d.jpg",
    )

    after_duplicates = find_duplicates(flickr_photo_ids=["53268016608"])
    assert after_duplicates == {
        "53268016608": {
            "id": "M139134318",
            "title": "File:Thameslink_Class_700_in_Pride_livery.jpg",
        }
    }
