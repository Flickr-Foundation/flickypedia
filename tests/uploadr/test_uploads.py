from datetime import datetime

from flask import Flask
from flickr_photos_api import SinglePhoto

from flickypedia.apis import WikimediaApi
from flickypedia.duplicates import find_duplicates
from flickypedia.structured_data import create_sdc_claims_for_new_flickr_photo
from flickypedia.uploadr.uploads import upload_single_photo


def test_upload_single_photo(app: Flask, wikimedia_api: WikimediaApi) -> None:
    before_duplicates = find_duplicates(flickr_photo_ids=["53370809793"])
    assert before_duplicates == {}

    photo: SinglePhoto = {
        "id": "53370809793",
        "url": "https://www.flickr.com/photos/199246608@N02/53370809793",
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
                "source": "https://live.staticflickr.com/65535/53370809793_dc5cb614ab_o_d.jpg",
                "media": "photo",
                "width": 4032,
                "height": 3024,
            }
        ],
        "title": None,
        "description": None,
        "date_posted": datetime.fromtimestamp(1701532872),
        "date_taken": {
            "value": datetime(2021, 9, 22, 18, 3, 10),
            "granularity": "second",
        },
        "safety_level": "safe",
        "original_format": "jpg",
        "tags": [],
        "machine_tags": {},
        "location": None,
        "secret": "-1",
        "server": "-1",
        "farm": "-1",
        "count_comments": 0,
        "count_views": 0,
        "media": "photo",
    }

    upload_single_photo(
        wikimedia_api,
        request={
            "photo": photo,
            "sdc": create_sdc_claims_for_new_flickr_photo(
                photo, retrieved_at=datetime(2023, 12, 2, 16, 2, 0)
            ),
            "title": "Floor decoration at St Giles In The Fields.jpg",
            "caption": {
                "language": "en",
                "text": "A circular floor pattern in St Giles In the Fields church, in London.",
            },
            "categories": ["Interiors of churches"],
            "username": "Alexwlchan",
        },
    )

    after_duplicates = find_duplicates(flickr_photo_ids=["53370809793"])
    assert after_duplicates == {
        "53370809793": {
            "id": "M141641035",
            "title": "File:Floor_decoration_at_St_Giles_In_The_Fields.jpg",
        }
    }
