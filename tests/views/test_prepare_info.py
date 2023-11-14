from flask import Flask
from flask.testing import FlaskClient
import pytest

from flickypedia.apis.flickr import SinglePhotoData, PhotosInAlbumData
from flickypedia.views.select_photos import save_cached_photos_data
from flickypedia.views import truncate_description
from utils import minify, get_typed_fixture


@pytest.mark.parametrize(
    "url",
    [
        "/prepare_info",
        "/prepare_info?selected_photo_ids=",
        "/prepare_info?selected_photo_ids=123",
        "/prepare_info?cache_id=123",
        "/prepare_info?selected_photo_ids=&cache_id=123",
    ],
)
def test_rejects_pages_with_bad_query_params(
    logged_in_client: FlaskClient, url: str
) -> None:
    resp = logged_in_client.get(url)

    assert resp.status_code == 400


def test_renders_form_for_single_photo(
    logged_in_client: FlaskClient, app: Flask, vcr_cassette: str
) -> None:
    get_photos_data = get_typed_fixture(
        path="flickr_api/single_photo-32812033543.json", model=SinglePhotoData
    )

    cache_id = save_cached_photos_data(get_photos_data)

    resp = logged_in_client.get(
        f"/prepare_info?selected_photo_ids=32812033543&cache_id={cache_id}",
    )

    assert resp.status_code == 200
    assert b"Puppy Kisses" in resp.data

    assert b"1 of 1" in resp.data

    assert "please set the language you’ll be using to write your caption:" in minify(
        resp.data
    )
    assert "please add a title and short caption" in minify(resp.data)


def test_renders_form_for_multiple_photo(
    logged_in_client: FlaskClient, app: Flask, vcr_cassette: str
) -> None:
    get_photos_data = get_typed_fixture(
        path="flickr_api/album-72177720312192106.json", model=PhotosInAlbumData
    )

    cache_id = save_cached_photos_data(get_photos_data)

    resp = logged_in_client.get(
        f"/prepare_info?selected_photo_ids=53285005734,53283740177&cache_id={cache_id}",
    )

    assert resp.status_code == 200
    assert b"ICANN78-AtLarge EURALO Plenary-100" in resp.data
    assert b"ICANN78-AtLarge EURALO Plenary-110" in resp.data

    # Test that we get the "X of Y" counter overlaid on the preview images
    assert b"1 of 2" in resp.data
    assert b"2 of 2" in resp.data

    assert "please set the language you’ll be using to write your captions:" in minify(
        resp.data
    )
    assert "please add titles and captions for each photo" in minify(resp.data)


def test_blocks_uploads_with_an_invalid_title(
    logged_in_client: FlaskClient, app: Flask, vcr_cassette: str
) -> None:
    get_photos_data = get_typed_fixture(
        path="flickr_api/single_photo-32812033543.json", model=SinglePhotoData
    )

    cache_id = save_cached_photos_data(get_photos_data)

    resp = logged_in_client.post(
        f"/prepare_info?selected_photo_ids=32812033543&cache_id={cache_id}",
        data={
            "photo_32812033543-title": "a" * 240,
            "photo_32812033543-short_caption": "A photo with a very long title",
            "photo_32812033543-categories": "",
        },
    )

    assert resp.status_code == 200
    assert b"Please choose a title which is less than 240 bytes" in resp.data


def test_blocks_uploads_with_a_too_long_caption(
    logged_in_client: FlaskClient, app: Flask, vcr_cassette: str
) -> None:
    get_photos_data = get_typed_fixture(
        path="flickr_api/single_photo-32812033543.json", model=SinglePhotoData
    )

    cache_id = save_cached_photos_data(get_photos_data)

    resp = logged_in_client.post(
        f"/prepare_info?selected_photo_ids=32812033543&cache_id={cache_id}",
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
        ("1\n2\n3\n4\n5\n6\n7\n", "1\n2\n3\n4\n5…"),
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
def test_truncate_description(original: str, truncated: str) -> None:
    assert truncate_description(original) == truncated


def test_escapes_html_in_description(logged_in_client: FlaskClient, app: Flask) -> None:
    """
    Flickr photos can contain HTML tags.

    In theory it's only a small subset of tags [1], but we escape all
    of them rather than risk unescaped HTML being rendered in our UI.

    [1]: https://www.flickr.com/html.gne

    """
    get_photos_data = get_typed_fixture(
        path="flickr_api/single_photo-4452100167.json", model=SinglePhotoData
    )

    cache_id = save_cached_photos_data(get_photos_data)

    resp = logged_in_client.get(
        f"/prepare_info?selected_photo_ids=4452100167&cache_id={cache_id}",
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
