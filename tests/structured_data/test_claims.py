import datetime

from flickr_photos_api import FlickrApi, SinglePhoto

from flickypedia.structured_data import (
    WikidataProperties,
    create_sdc_claims_for_existing_flickr_photo,
    create_sdc_claims_for_new_flickr_photo,
)
from utils import get_claims_fixture


def test_create_sdc_claims_for_flickr_photo_without_date_taken() -> None:
    photo: SinglePhoto = {
        "id": "53248015596",
        "url": "https://www.flickr.com/photos/199246608@N02/53248015596/",
        "owner": {
            "id": "199246608@N02",
            "username": "cefarrjf87",
            "realname": "Alex Chan",
            "path_alias": None,
            "photos_url": "https://www.flickr.com/photos/199246608@N02/",
            "profile_url": "https://www.flickr.com/people/199246608@N02/",
        },
        "title": "IMG_6027",
        "description": None,
        "sizes": [
            {
                "label": "Original",
                "source": "https://live.staticflickr.com/65535/53248015596_c03f8123cf_o_d.jpg",
                "media": "photo",
                "width": 4032,
                "height": 3024,
            }
        ],
        "license": {
            "id": "cc-by-2.0",
            "label": "CC BY 2.0",
            "url": "https://creativecommons.org/licenses/by/2.0/",
        },
        "date_posted": datetime.datetime.fromtimestamp(1696939706),
        "date_taken": None,
        "safety_level": "safe",
        "original_format": "jpg",
        "tags": [],
        "location": None,
        "secret": "-1",
        "server": "-1",
        "farm": "-1",
        "count_comments": 0,
        "count_views": 0,
    }

    actual = create_sdc_claims_for_new_flickr_photo(
        photo=photo, retrieved_at=datetime.datetime(2023, 11, 14, 16, 15, 0)
    )
    expected = get_claims_fixture("photo_53248015596.json")

    assert actual == expected


def test_create_sdc_claims_for_flickr_photo_with_date_taken() -> None:
    photo: SinglePhoto = {
        "id": "53234140350",
        "url": "https://www.flickr.com/photos/mdgovpics/53234140350/",
        "owner": {
            "id": "64018555@N03",
            "username": "MDGovpics",
            "realname": "Maryland GovPics",
            "path_alias": "mdgovpics",
            "photos_url": "https://www.flickr.com/photos/mdgovpics/",
            "profile_url": "https://www.flickr.com/people/mdgovpics/",
        },
        "title": "UMD Class Visits",
        "description": "Lt. Governor Aruna visits classes at University of Maryland by Joe Andrucyk at Thurgood Marshall Hall, 7805 Regents Dr, College Park MD 20742",
        "sizes": [
            {
                "label": "Original",
                "source": "https://live.staticflickr.com/65535/53234140350_93579322a9_o_d.jpg",
                "media": "photo",
                "width": 6192,
                "height": 4128,
            }
        ],
        "license": {
            "id": "cc-by-2.0",
            "label": "CC BY 2.0",
            "url": "https://creativecommons.org/licenses/by/2.0/",
        },
        "date_posted": datetime.datetime.fromtimestamp(1696421915),
        "date_taken": {
            "value": datetime.datetime(2023, 10, 3, 5, 45, 0),
            "granularity": "second",
        },
        "safety_level": "safe",
        "original_format": "jpg",
        "tags": [],
        "location": None,
        "secret": "-1",
        "server": "-1",
        "farm": "-1",
        "count_comments": 0,
        "count_views": 0,
    }

    actual = create_sdc_claims_for_new_flickr_photo(
        photo=photo, retrieved_at=datetime.datetime(2023, 11, 14, 16, 15, 0)
    )
    expected = get_claims_fixture("photo_53234140350.json")

    assert actual == expected


def test_creates_sdc_for_photo_with_in_copyright_license() -> None:
    photo: SinglePhoto = {
        "id": "15602283025",
        "url": "https://www.flickr.com/photos/golfking1/15602283025/",
        "owner": {
            "id": "57778372@N04",
            "username": "airplanes_uk",
            "realname": "Jonathan Palombo",
            "path_alias": "golfking1",
            "photos_url": "https://www.flickr.com/photos/golfking1/",
            "profile_url": "https://www.flickr.com/people/golfking1/",
        },
        "title": "EI-DYY",
        "description": None,
        "sizes": [
            {
                "label": "Large 1024",
                "source": "https://live.staticflickr.com/3943/15602283025_fd7d8b0dd9_b.jpg",
                "media": "photo",
                "width": 1024,
                "height": 839,
            }
        ],
        "license": {"id": "in-copyright", "label": "All Rights Reserved", "url": None},
        "date_posted": datetime.datetime.fromtimestamp(1414001923),
        "date_taken": {
            "value": datetime.datetime(2014, 7, 14, 7, 56, 51),
            "granularity": "second",
        },
        "safety_level": "safe",
        "original_format": "jpg",
        "tags": [],
        "location": None,
        "secret": "-1",
        "server": "-1",
        "farm": "-1",
        "count_comments": 0,
        "count_views": 0,
    }

    actual = create_sdc_claims_for_existing_flickr_photo(photo)
    expected = get_claims_fixture("photo_15602283025.json")

    assert actual == expected


def test_omits_url_for_existing_photo(flickr_api: FlickrApi) -> None:
    photo = flickr_api.get_single_photo(photo_id="383861611")

    new_sdc = create_sdc_claims_for_new_flickr_photo(
        photo, retrieved_at=datetime.datetime.now()
    )
    existing_sdc = create_sdc_claims_for_existing_flickr_photo(photo)

    new_source_statement = next(
        s
        for s in new_sdc["claims"]
        if s["mainsnak"]["property"] == WikidataProperties.SourceOfFile
    )
    existing_source_statement = next(
        s
        for s in existing_sdc["claims"]
        if s["mainsnak"]["property"] == WikidataProperties.SourceOfFile
    )

    # Check we include the URL qualifier for new SDC…
    assert WikidataProperties.Url in new_source_statement["qualifiers"]

    # …but not for SDC on existing photos
    assert WikidataProperties.Url not in existing_source_statement["qualifiers"]
