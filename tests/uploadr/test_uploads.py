import datetime

from flask import Flask
from flickypedia.apis.flickr_photos_api import SinglePhoto

from flickypedia.apis.wikimedia import WikimediaApi
from flickypedia.duplicates import find_duplicates
from flickypedia.apis.structured_data import create_sdc_claims_for_flickr_photo
from flickypedia.uploadr.uploads import upload_single_photo


def test_upload_single_photo(app: Flask, wikimedia_api: WikimediaApi) -> None:
    before_duplicates = find_duplicates(flickr_photo_ids=["53268016608"])
    assert before_duplicates == {}

    photo: SinglePhoto = {
        "id": "53268016608",
        "url": "https://www.flickr.com/photos/199246608@N02/53268016608",
        "owner": {
            "id": "199246608@N02",
            "username": "cefarrjf87",
            "realname": "Alex Chan",
            "path_alias": None,
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
        },
        "safety_level": "safe",
        "original_format": "jpg",
        "tags": [],
        "location": None,
    }

    upload_single_photo(
        wikimedia_api,
        request={
            "photo": photo,
            "sdc": create_sdc_claims_for_flickr_photo(
                photo, retrieved_at=datetime.datetime(2023, 11, 14, 16, 16, 0)
            ),
            "title": "Thameslink Class 700 in Pride livery.jpg",
            "caption": {
                "language": "en",
                "text": "A Thameslink Class 700 train in the rainbow Pride livery, taken at night",
            },
            "categories": [],
            "username": "TestUser",
        },
    )

    after_duplicates = find_duplicates(flickr_photo_ids=["53268016608"])
    assert after_duplicates == {
        "53268016608": {
            "id": "M139134318",
            "title": "File:Thameslink_Class_700_in_Pride_livery.jpg",
        }
    }
