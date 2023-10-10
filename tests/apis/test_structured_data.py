import json

import pytest

from flickypedia.apis.structured_data import (
    create_copyright_status_data,
    create_flickr_creator_data,
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
