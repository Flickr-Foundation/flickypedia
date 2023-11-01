import pytest


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


def test_renders_form_for_single_photo(logged_in_client, app, vcr_cassette):
    cache_dir = app.config["FLICKR_API_RESPONSE_CACHE"]

    with open("tests/fixtures/flickr_api/single_photo-32812033544.json") as in_file:
        with open(f"{cache_dir}/1234567890.json", "w") as out_file:
            out_file.write('{"value": %s}' % in_file.read())

    resp = logged_in_client.get(
        "/prepare_info?selected_photo_ids=32812033543&cached_api_response_id=1234567890",
    )

    assert resp.status_code == 200
    assert b"Puppy Kisses" in resp.data


def test_renders_form_for_multiple_photo(logged_in_client, app, vcr_cassette):
    cache_dir = app.config["FLICKR_API_RESPONSE_CACHE"]

    with open("tests/fixtures/flickr_api/album-72177720312192106.json") as in_file:
        with open(f"{cache_dir}/1234567890.json", "w") as out_file:
            out_file.write('{"value": %s}' % in_file.read())

    resp = logged_in_client.get(
        "/prepare_info?selected_photo_ids=53285005734,53283740177&cached_api_response_id=1234567890",
    )

    assert resp.status_code == 200
    assert b"ICANN78-AtLarge EURALO Plenary-100" in resp.data
    assert b"ICANN78-AtLarge EURALO Plenary-110" in resp.data


def test_blocks_uploads_with_an_invalid_title(logged_in_client, app, vcr_cassette):
    cache_dir = app.config["FLICKR_API_RESPONSE_CACHE"]

    with open("tests/fixtures/flickr_api/single_photo-32812033544.json") as in_file:
        with open(f"{cache_dir}/1234567890.json", "w") as out_file:
            out_file.write('{"value": %s}' % in_file.read())

    resp = logged_in_client.post(
        "/prepare_info?selected_photo_ids=32812033543&cached_api_response_id=1234567890",
        data={
            "photo_32812033543-title": "a" * 240,
            "photo_32812033543-short_caption": "A photo with a very long title",
            "photo_32812033543-categories": "",
        },
    )

    assert resp.status_code == 200
    assert b"Please choose a title which is less than 240 bytes" in resp.data
