import datetime

from flask import Flask
from flickr_photos_api import SinglePhoto

from flickypedia.apis.wikimedia import WikimediaApi
from flickypedia.duplicates import find_duplicates
from flickypedia.uploads import upload_single_image


def test_upload_single_image(app: Flask, wikimedia_api: WikimediaApi) -> None:
    before_duplicates = find_duplicates(flickr_photo_ids=["53268016608"])
    assert before_duplicates == {}

    photo: SinglePhoto = {
        "id": "53268016608",
        "url": "https://www.flickr.com/photos/199246608@N02/53268016608",
        "owner": {
            "id": "199246608@N02",
            "username": "cefarrjf87",
            "realname": "Alex Chan",
            "photos_url": "https://www.flickr.com/photos/199246608@N02/",
            "profile_url": "https://www.flickr.com/people/199246608@N02/",
        },
        "license": {
            "id": "cc-by-2.0",
            "label": "CC BY 2.0",
            "url": "https://creativecommons.org/licenses/by/2.0/",
        },
        "sizes": [
            {
                "label": "Original",
                "source": "https://live.staticflickr.com/65535/53268016608_5b890124fd_o_d.jpg",
                "media": "photo",
                "width": -1,
                "height": -1,
            }
        ],
        "title": None,
        "description": None,
        "date_posted": datetime.datetime.fromtimestamp(1697645772),
        "date_taken": {
            "value": datetime.datetime(2023, 9, 12, 19, 54, 32),
            "granularity": "second",
            "unknown": False,
        },
        "safety_level": "safe",
        "original_format": "jpeg",
    }

    upload_single_image(
        wikimedia_api,
        photo=photo,
        filename="Thameslink Class 700 in Pride livery.jpg",
        file_caption_language="en",
        file_caption="A Thameslink Class 700 train in the rainbow Pride livery, taken at night",
    )

    after_duplicates = find_duplicates(flickr_photo_ids=["53268016608"])
    assert after_duplicates == {
        "53268016608": {
            "id": "M139134318",
            "title": "File:Thameslink_Class_700_in_Pride_livery.jpg",
        }
    }
