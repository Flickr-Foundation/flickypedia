import json

import pytest

from flickypedia.apis.structured_data import (
    create_license_statement,
    create_copyright_status_data,
    create_flickr_creator_data,
    create_source_data_for_photo,
)


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
    expected = json.load(open(f"tests/fixtures/structured_data/{filename}"))

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
    expected = json.load(open(f"tests/fixtures/structured_data/{filename}"))

    assert result == expected


def test_create_source_data_for_photo():
    result = create_source_data_for_photo(
        user_id="199246608@N02",
        photo_id="53248015596",
        jpeg_url="https://live.staticflickr.com/65535/53248015596_c03f8123cf_o_d.jpg",
    )
    expected = json.load(open("tests/fixtures/structured_data/photo_source_data.json"))

    assert result == expected


@pytest.mark.parametrize(
    ["license_id", "filename"], [("cc-by-2.0", "license_cc_by_2.0.json")]
)
def test_create_license_statement(license_id, filename):
    actual = create_license_statement(license_id)
    expected = json.load(open(f"tests/fixtures/structured_data/{filename}"))

    assert actual == expected


def test_create_license_statement_fails_if_unrecognised_license():
    with pytest.raises(ValueError, match="Unrecognised license ID"):
        create_license_statement(license_id="mystery")
