from datetime import datetime, timezone

from flickr_api import FlickrApi
import pytest

from flickypedia.apis.flickr import get_single_photo
from flickypedia.structured_data import (
    WikidataProperties,
    create_sdc_claims_for_existing_flickr_photo,
    create_sdc_claims_for_new_flickr_photo,
)
from flickypedia.types.flickr import FlickrPhoto
from utils import get_claims_fixture


def test_create_sdc_claims_for_flickr_photo_without_date_taken() -> None:
    photo: FlickrPhoto = {
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
        "date_posted": datetime.fromtimestamp(1696939706),
        "date_taken": None,
        "safety_level": "safe",
        "original_format": "jpg",
        "tags": [],
        "machine_tags": {},
        "location": None,
    }

    actual = create_sdc_claims_for_new_flickr_photo(
        photo=photo, retrieved_at=datetime(2023, 11, 14, 16, 15, 0)
    )
    expected = get_claims_fixture("photo_53248015596.json")

    assert actual == expected


def test_create_sdc_claims_for_flickr_photo_with_date_taken() -> None:
    photo: FlickrPhoto = {
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
        "date_posted": datetime.fromtimestamp(1696421915),
        "date_taken": {
            "value": datetime(2023, 10, 3, 5, 45, 0),
            "granularity": "second",
        },
        "safety_level": "safe",
        "original_format": "jpg",
        "tags": [],
        "machine_tags": {},
        "location": None,
    }

    actual = create_sdc_claims_for_new_flickr_photo(
        photo=photo, retrieved_at=datetime(2023, 11, 14, 16, 15, 0)
    )
    expected = get_claims_fixture("photo_53234140350.json")

    assert actual == expected


def test_creates_sdc_for_photo_with_in_copyright_license() -> None:
    photo: FlickrPhoto = {
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
        "license": {
            "id": "all-rights-reserved",
            "label": "All Rights Reserved",
            "url": "https://www.flickrhelp.com/hc/en-us/articles/10710266545556-Using-Flickr-images-shared-by-other-members",
        },
        "date_posted": datetime.fromtimestamp(1414001923),
        "date_taken": {
            "value": datetime(2014, 7, 14, 7, 56, 51),
            "granularity": "second",
        },
        "safety_level": "safe",
        "original_format": "jpg",
        "tags": [],
        "machine_tags": {},
        "location": None,
    }

    actual = create_sdc_claims_for_existing_flickr_photo(photo)
    expected = get_claims_fixture("photo_15602283025.json")

    assert actual == expected


@pytest.mark.parametrize(
    "photo_id, license_id",
    [
        ("43686615590", "cc-by-4.0"),
        ("53167940017", "cc-by-sa-4.0"),
    ],
)
def test_create_sdc_for_cc_by_4_photo(
    flickr_api: FlickrApi, photo_id: str, license_id: str
) -> None:
    """
    Create structured data claims for a photo with a CC 4 license.
    """
    photo = get_single_photo(flickr_api, photo_id=photo_id)
    assert photo["license"]["id"] == license_id

    create_sdc_claims_for_new_flickr_photo(
        photo, retrieved_at=datetime.now(tz=timezone.utc)
    )


def test_omits_url_for_existing_photo(flickr_api: FlickrApi) -> None:
    photo = get_single_photo(flickr_api, photo_id="383861611")

    new_sdc = create_sdc_claims_for_new_flickr_photo(
        photo, retrieved_at=datetime.now(tz=timezone.utc)
    )
    existing_sdc = create_sdc_claims_for_existing_flickr_photo(photo)

    new_source_statement = [
        s
        for s in new_sdc["claims"]
        if s["mainsnak"]["property"] == WikidataProperties.SourceOfFile
    ][0]
    existing_source_statement = [
        s
        for s in existing_sdc["claims"]
        if s["mainsnak"]["property"] == WikidataProperties.SourceOfFile
    ][0]

    # Check we include the URL qualifier for new SDC…
    assert WikidataProperties.Url in new_source_statement["qualifiers"]

    # …but not for SDC on existing photos
    assert WikidataProperties.Url not in existing_source_statement["qualifiers"]
