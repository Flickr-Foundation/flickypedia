import os

import pytest
import vcr

from flickypedia.apis.wikimedia import WikimediaApiException, get_userinfo


def test_get_userinfo():
    with vcr.use_cassette(
        "test_get_userinfo.yml",
        cassette_library_dir="tests/fixtures/cassettes",
        filter_headers=["authorization"],
        record_mode="once",
    ):
        info = get_userinfo(access_token=os.environ.get("ACCESS_TOKEN", "<unknown>"))

        assert info == {"id": 829939, "name": "Alexwlchan"}


def test_get_userinfo_with_bad_token():
    with vcr.use_cassette(
        "test_get_userinfo_with_bad_token.yml",
        cassette_library_dir="tests/fixtures/cassettes",
        filter_headers=["authorization"],
        record_mode="once",
    ):
        with pytest.raises(WikimediaApiException, match="Invalid access token") as exc:
            get_userinfo(access_token="not_a_real_token")

        assert exc.value.code == "mwoauth-invalid-authorization"
