import os

import vcr

from flickypedia.apis.wikimedia import get_userinfo


def test_get_userinfo():
    with vcr.use_cassette(
        "test_get_userinfo.yml",
        cassette_library_dir="tests/fixtures/cassettes",
        filter_headers=["authorization"],
        record_mode="once",
    ):
        info = get_userinfo(access_token=os.environ.get("ACCESS_TOKEN", "<unknown>"))

        assert info == {"id": 829939, "name": "Alexwlchan"}
