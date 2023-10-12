import datetime
import json
import os

import pytest

from flickypedia.apis.structured_data import (
    create_date_taken_statement,
    create_license_statement,
    create_copyright_status_data,
    create_flickr_creator_data,
    create_source_data_for_photo,
    create_uploaded_to_flickr_statement,
)


def get_fixture(filename):
    with open(os.path.join("tests/fixtures/structured_data", filename)) as f:
        return json.load(f)


@pytest.mark.parametrize(
    ["kwargs", "filename"],
    [
        (
            {"user_id": "47397743@N05", "username": None, "realname": "WNDC"},
            "creator_Q7986087.json",
        ),
        (
            {"user_id": "199246608@N02", "username": "Alex Chan", "realname": None},
            "creator_AlexChan.json",
        ),
        (
            {
                "user_id": "35591378@N03",
                "username": "Obama White House Archived",
                "realname": None,
            },
            "creator_ObamaWhiteHouse.json",
        ),
    ],
)
def test_create_flickr_creator_data(vcr_cassette, kwargs, filename):
    result = create_flickr_creator_data(**kwargs)
    expected = get_fixture(filename)

    assert result == expected


def test_create_copyright_status_data_fails_for_unknown_value():
    with pytest.raises(ValueError, match="Unable to map a copyright status"):
        create_copyright_status_data(status="No known copyright status")


@pytest.mark.parametrize(
    ["kwargs", "filename"],
    [
        ({"status": "copyrighted"}, "copyright_status_copyrighted.json"),
    ],
)
def test_create_copyright_status_data(kwargs, filename):
    result = create_copyright_status_data(**kwargs)
    expected = get_fixture(filename)

    assert result == expected


def test_create_source_data_for_photo():
    result = create_source_data_for_photo(
        user_id="199246608@N02",
        photo_id="53248015596",
        jpeg_url="https://live.staticflickr.com/65535/53248015596_c03f8123cf_o_d.jpg",
    )
    expected = get_fixture("photo_source_data.json")

    assert result == expected


@pytest.mark.parametrize(
    ["license_id", "filename"], [("cc-by-2.0", "license_cc_by_2.0.json")]
)
def test_create_license_statement(license_id, filename):
    actual = create_license_statement(license_id)
    expected = get_fixture(filename)

    assert actual == expected


def test_create_license_statement_fails_if_unrecognised_license():
    with pytest.raises(ValueError, match="Unrecognised license ID"):
        create_license_statement(license_id="mystery")


def test_create_uploaded_to_flickr_statement():
    actual = create_uploaded_to_flickr_statement(
        uploaded_date=datetime.datetime(2023, 10, 12)
    )
    expected = get_fixture("date_uploaded_to_flickr.json")

    assert actual == expected


@pytest.mark.parametrize(
    ["date_taken", "taken_granularity", "filename"],
    [
        # Based on https://www.flickr.com/photos/184374196@N07/53069446440
        (datetime.datetime(2023, 2, 20, 23, 32, 31), 0, "date_taken_YYYY-MM-DD.json"),
        # Based on https://www.flickr.com/photos/normko/361850789
        (datetime.datetime(1970, 3, 1, 0, 0, 0), 4, "date_taken_YYYY-MM.json"),
        # Based on https://www.flickr.com/photos/nationalarchives/5240741057
        (datetime.datetime(1950, 1, 1, 0, 0, 0), 6, "date_taken_YYYY.json"),
        # Based on https://www.flickr.com/photos/nlireland/6975991819
        (datetime.datetime(1910, 1, 1, 0, 0, 0), 8, "date_taken_circa.json"),
    ],
)
def test_create_date_taken_statement(date_taken, taken_granularity, filename):
    actual = create_date_taken_statement(date_taken, taken_granularity)
    expected = get_fixture(filename)

    assert actual == expected


def test_create_date_taken_statement_fails_on_unrecognised_granularity():
    with pytest.raises(ValueError, match="Unrecognised taken_granularity"):
        create_date_taken_statement(
            date_taken=datetime.datetime.now(), taken_granularity=-1
        )
