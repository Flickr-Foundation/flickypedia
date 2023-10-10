import json

import pytest

from flickypedia.apis.structured_data import create_flickr_creator_data


@pytest.mark.parametrize(
    ["kwargs", "filename"],
    [
        (
            {"user_id": "47397743@N05", "username": None, "realname": "WNDC"},
            "creator_Q7986087.json",
        ),
        (
            {"user_id": "199246608@N02", "username": None, "realname": "Alex Chan"},
            "creator_AlexChan.json",
        ),
    ],
)
def test_create_flickr_creator_data(vcr_cassette, kwargs, filename):
    result = create_flickr_creator_data(**kwargs)
    expected = json.load(open(f"tests/fixtures/structured_data/{filename}"))

    assert result == expected
