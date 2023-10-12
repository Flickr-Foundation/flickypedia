import datetime
import json
import os

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
def test_create_flickr_creator_statement(vcr_cassette, kwargs, filename):
    result = create_flickr_creator_statement(**kwargs)
    expected = get_fixture(filename)

    assert result == expected


def test_create_copyright_status_statement_fails_for_unknown_value():
    with pytest.raises(ValueError, match="Unable to map a copyright status"):
        create_copyright_status_statement(status="No known copyright status")


@pytest.mark.parametrize(
    ["kwargs", "filename"],
    [
        ({"status": "copyrighted"}, "copyright_status_copyrighted.json"),
    ],
)
def test_create_copyright_status_statement(kwargs, filename):
    result = create_copyright_status_statement(**kwargs)
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


def test_create_posted_to_flickr_statement():
    actual = create_posted_to_flickr_statement(
        posted_date=datetime.datetime(2023, 10, 12)
    )
    expected = get_fixture("date_posted_to_flickr.json")

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


def test_create_sdc_claims_for_flickr_photo_without_date_taken(vcr_cassette):
    # This test is based on
    # https://www.flickr.com/photos/199246608@N02/53248015596/
    actual = create_sdc_claims_for_flickr_photo(
        photo_id="53248015596",
        user_id="199246608@N02",
        username="cefarrjf87",
        realname="Alex Chan",
        copyright_status="copyrighted",
        jpeg_url="https://live.staticflickr.com/65535/53248015596_c03f8123cf_o_d.jpg",
        license_id="cc-by-2.0",
        posted_date=datetime.datetime.fromtimestamp(1696939706),
        date_taken=datetime.datetime(2023, 10, 10, 5, 8, 21),
        taken_unknown=True,
        taken_granularity=0
    )
    expected = get_fixture("photo_53248015596.json")

    assert actual == expected
