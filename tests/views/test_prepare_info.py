import json
import shutil

import pytest

from utils import minify


@pytest.mark.parametrize(
    "url",
    [
        "/prepare_info",
        "/prepare_info?selected_photo_ids=",
        "/prepare_info?selected_photo_ids=123",
        "/prepare_info?cached_api_response_id=123",
        "/prepare_info?selected_photo_ids=&cached_api_response_id=123",
    ],
)
def test_rejects_pages_with_bad_query_params(logged_in_client, url):
    resp = logged_in_client.get(url)

    assert resp.status_code == 400


def test_renders_form_for_single_photo(logged_in_client, app, flickr_api):
    cache_dir = app.config["FLICKR_API_RESPONSE_CACHE"]

    with open(f"{cache_dir}/1234567890.json", "w") as outfile:
        with open("tests/fixtures/flickr_api/32812033543.json") as infile:
            single_photo_resp = json.load(infile)
        outfile.write(json.dumps({"photos": [single_photo_resp]}))

    resp = logged_in_client.get(
        "/prepare_info?selected_photo_ids=32812033543&cached_api_response_id=1234567890",
    )

    assert resp.status_code == 200
    assert b"Puppy Kisses" in resp.data


def test_renders_form_for_multiple_photo(logged_in_client, app, flickr_api):
    cache_dir = app.config["FLICKR_API_RESPONSE_CACHE"]

    shutil.copyfile(
        "tests/fixtures/flickr_api/album-72177720312192106.json",
        f"{cache_dir}/1234567890.json",
    )

    resp = logged_in_client.get(
        "/prepare_info?selected_photo_ids=53285005734,53283740177&cached_api_response_id=1234567890",
    )

    assert resp.status_code == 200
    assert b"ICANN78-AtLarge EURALO Plenary-100" in resp.data
    assert b"ICANN78-AtLarge EURALO Plenary-110" in resp.data
