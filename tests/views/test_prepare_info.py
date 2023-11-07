import pytest

from flickypedia.views import truncate_description


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

    assert b"1 of 1" in resp.data

    assert b"please set the language you’ll be using to write your caption:" in resp.data
    assert b"please add a title and short caption" in resp.data


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

    # Test that we get the "X of Y" counter overlaid on the preview images
    assert b"1 of 2" in resp.data
    assert b"2 of 2" in resp.data

    assert b"please set the language you’ll be using to write your captions:" in resp.data
    assert b"please set titles and captions for each photo" in resp.data


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


def test_blocks_uploads_with_a_too_long_caption(logged_in_client, app, vcr_cassette):
    cache_dir = app.config["FLICKR_API_RESPONSE_CACHE"]

    with open("tests/fixtures/flickr_api/single_photo-32812033544.json") as in_file:
        with open(f"{cache_dir}/1234567890.json", "w") as out_file:
            out_file.write('{"value": %s}' % in_file.read())

    resp = logged_in_client.post(
        "/prepare_info?selected_photo_ids=32812033543&cached_api_response_id=1234567890",
        data={
            "photo_32812033543-title": "A photo with a reasonable title",
            "photo_32812033543-short_caption": "A photo with a very long caption" * 100,
            "photo_32812033543-categories": "",
        },
    )

    assert resp.status_code == 200


@pytest.mark.parametrize(
    ["original", "truncated"],
    [
        # A description which is split across many lines
        ("1\n2\n3\n4\n5\n6\n7\n", "1\n2\n3\n4\n5"),
        # A description which is short enough to be returned unmodified
        ("A blue train in a green field", "A blue train in a green field"),
        # A description which is around the target length
        ("a" * 161, "a" * 161),
        ("a" * 170, "a" * 170),
        # A description which is comfortably over the target length, truncated
        # at the right word.
        (
            "a" * 150 + " and now we have some words to push us towards the end",
            "a" * 150 + " and now we have some…",
        ),
        # A description which is comfortably over the target length, truncated
        # just before a line break.
        (
            "a" * 150 + " and now we have\nsome words to push us towards the end",
            "a" * 150 + " and now we have…",
        ),
    ],
)
def test_truncate_description(original, truncated):
    assert truncate_description(original) == truncated


def test_escapes_html_in_description(logged_in_client, app):
    """
    Flickr photos can contain HTML tags.

    In theory it's only a small subset of tags [1], but we escape all
    of them rather than risk unescaped HTML being rendered in our UI.

    [1]: https://www.flickr.com/html.gne

    """
    cache_dir = app.config["FLICKR_API_RESPONSE_CACHE"]

    with open("tests/fixtures/flickr_api/single_photo-4452100167.json") as in_file:
        with open(f"{cache_dir}/4452100167.json", "w") as out_file:
            out_file.write('{"value": %s}' % in_file.read())

    resp = logged_in_client.get(
        "/prepare_info?selected_photo_ids=4452100167&cached_api_response_id=4452100167",
    )

    assert (
        b"These textures are posted with the Attribution Creative Commons license.\n"
        b"&lt;b&gt;Credit must be given if used.&lt;/b&gt;\n\n"
        b"Copy this Credit Line:"
    ) in resp.data

    assert (
        b"These textures are posted with the Attribution Creative Commons license.\n"
        b"<b>Credit must be given if used.</b>\n\n"
        b"Copy this Credit Line:"
    ) not in resp.data
