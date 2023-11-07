import datetime
import json
import os
from typing import Any

from flask import Flask
from flickr_photos_api import SinglePhoto, TakenGranularity, User as FlickrUser
import pytest

from flickypedia.apis.structured_data import (
    create_date_taken_statement,
    create_license_statement,
    create_copyright_status_statement,
    create_flickr_creator_statement,
    create_source_data_for_photo,
    create_posted_to_flickr_statement,
    create_sdc_claims_for_flickr_photo,
)


def get_fixture(filename: str) -> Any:
    with open(os.path.join("tests/fixtures/structured_data", filename)) as f:
        return json.load(f)


@pytest.mark.parametrize(
    ["user", "filename"],
    [
        pytest.param(
            {
                "id": "47397743@N05",
                "username": None,
                "realname": "WNDC",
                "photos_url": "https://www.flickr.com/photos/west_northamptonshire_development_corporation/",
                "profile_url": "https://www.flickr.com/people/west_northamptonshire_development_corporation/",
            },
            "creator_Q7986087.json",
            id="47397743@N05",
        ),
        pytest.param(
            {
                "id": "199246608@N02",
                "username": "Alex Chan",
                "realname": None,
                "photos_url": "https://www.flickr.com/photos/199246608@N02/",
                "profile_url": "https://www.flickr.com/people/199246608@N02/",
            },
            "creator_AlexChan.json",
            id="AlexChan",
        ),
        pytest.param(
            {
                "id": "35591378@N03",
                "username": "Obama White House Archived",
                "realname": None,
                "photos_url": "https://www.flickr.com/photos/obamawhitehouse/",
                "profile_url": "https://www.flickr.com/people/obamawhitehouse/",
            },
            "creator_ObamaWhiteHouse.json",
            id="ObamaWhiteHouse",
        ),
    ],
)
def test_create_flickr_creator_statement(
    app: Flask, vcr_cassette: str, user: FlickrUser, filename: str
) -> None:
    result = create_flickr_creator_statement(user)
    expected = get_fixture(filename)

    assert result == expected


def test_create_copyright_status_statement_fails_for_unknown_value() -> None:
    with pytest.raises(ValueError, match="Unable to map a copyright status"):
        create_copyright_status_statement(status="No known copyright status")


@pytest.mark.parametrize(
    ["status", "filename"],
    [
        ("copyrighted", "copyright_status_copyrighted.json"),
    ],
)
def test_create_copyright_status_statement(status: str, filename: str) -> None:
    result = create_copyright_status_statement(status=status)
    expected = get_fixture(filename)

    assert result == expected


def test_create_source_data_for_photo() -> None:
    result = create_source_data_for_photo(
        photo_url="https://www.flickr.com/photos/199246608@N02/53248015596/",
        original_url="https://live.staticflickr.com/65535/53248015596_c03f8123cf_o_d.jpg",
    )
    expected = get_fixture("photo_source_data.json")

    assert result == expected


@pytest.mark.parametrize(
    ["license_id", "filename"],
    [
        ("cc-by-2.0", "license_cc_by_2.0.json"),
        ("usgov", "license_usgov.json"),
        ("cc0-1.0", "license_cc0.json"),
    ],
)
def test_create_license_statement(license_id: str, filename: str) -> None:
    actual = create_license_statement(license_id)
    expected = get_fixture(filename)

    assert actual == expected


def test_can_create_license_statement_for_all_allowed_licenses(app: Flask) -> None:
    for license_id in app.config["ALLOWED_LICENSES"]:
        create_license_statement(license_id)


def test_create_license_statement_fails_if_unrecognised_license() -> None:
    with pytest.raises(ValueError, match="Unrecognised license ID"):
        create_license_statement(license_id="mystery")


def test_create_posted_to_flickr_statement() -> None:
    actual = create_posted_to_flickr_statement(
        date_posted=datetime.datetime(2023, 10, 12)
    )
    expected = get_fixture("date_posted_to_flickr.json")

    assert actual == expected


@pytest.mark.parametrize(
    ["date_taken", "granularity", "filename"],
    [
        # Based on https://www.flickr.com/photos/184374196@N07/53069446440
        (
            datetime.datetime(2023, 2, 20, 23, 32, 31),
            "second",
            "date_taken_YYYY-MM-DD.json",
        ),
        # Based on https://www.flickr.com/photos/normko/361850789
        (datetime.datetime(1970, 3, 1, 0, 0, 0), "month", "date_taken_YYYY-MM.json"),
        # Based on https://www.flickr.com/photos/nationalarchives/5240741057
        (datetime.datetime(1950, 1, 1, 0, 0, 0), "year", "date_taken_YYYY.json"),
        # Based on https://www.flickr.com/photos/nlireland/6975991819
        (datetime.datetime(1910, 1, 1, 0, 0, 0), "circa", "date_taken_circa.json"),
    ],
)
def test_create_date_taken_statement(
    date_taken: datetime.datetime, granularity: TakenGranularity, filename: str
) -> None:
    actual = create_date_taken_statement(
        date_taken={"value": date_taken, "granularity": granularity, "unknown": False}
    )
    expected = get_fixture(filename)

    assert actual == expected


def test_create_date_taken_statement_fails_on_unrecognised_granularity() -> None:
    with pytest.raises(ValueError, match="Unrecognised taken_granularity"):
        create_date_taken_statement(
            date_taken={
                "value": datetime.datetime.now(),
                "granularity": -1,  # type: ignore
                "unknown": False,
            }
        )


def test_create_sdc_claims_for_flickr_photo_without_date_taken(
    app: Flask, vcr_cassette: str
) -> None:
    photo: SinglePhoto = {
        "id": "53248015596",
        "url": "https://www.flickr.com/photos/199246608@N02/53248015596/",
        "owner": {
            "id": "199246608@N02",
            "username": "cefarrjf87",
            "realname": "Alex Chan",
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
                "height": 3024
            }
        ],
        "license": {
            "id": "cc-by-2.0",
            "label": "CC BY 2.0",
            "url": "https://creativecommons.org/licenses/by/2.0/",
        },
        "date_posted": datetime.datetime.fromtimestamp(1696939706),
        "date_taken": {
            "unknown": True,
        },
        "safety_level": "safe",
        "original_format": "jpg"
    }

    actual = create_sdc_claims_for_flickr_photo(photo=photo)
    expected = get_fixture("photo_53248015596.json")

    assert actual == expected


def test_create_sdc_claims_for_flickr_photo_with_date_taken(
    app: Flask, vcr_cassette: str
) -> None:
    photo: SinglePhoto = {
        "id": "53234140350",
        "url": "https://www.flickr.com/photos/mdgovpics/53234140350/",
        "owner": {
            "id": "64018555@N03",
            "username": "MDGovpics",
            "realname": "Maryland GovPics",
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
                "height": 4128
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
            "unknown": False,
            "granularity": "second",
        },
        "safety_level": "safe",
        "original_format": "jpg"
    }

    actual = create_sdc_claims_for_flickr_photo(photo=photo)
    expected = get_fixture("photo_53234140350.json")

    assert actual == expected
