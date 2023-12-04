from flask import Flask
from flask.testing import FlaskClient
import pytest
from werkzeug.test import TestResponse

from flickypedia.apis.flickr import SinglePhotoData, PhotosInAlbumData
from flickypedia.uploadr.caching import save_cached_photos_data
from flickypedia.uploadr.uploads import uploads_queue, UploadRequest
from flickypedia.uploadr.views.prepare_info import (
    truncate_description,
    TruncationResult,
)
from utils import minify, get_typed_fixture


def get_single_photo_cache_id() -> str:
    get_photos_data = get_typed_fixture(
        path="flickr_api/single_photo-32812033543.json", model=SinglePhotoData
    )

    return save_cached_photos_data(get_photos_data)


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
    logged_in_client: FlaskClient, vcr_cassette: str
) -> None:
    cache_id = get_single_photo_cache_id()

    resp = logged_in_client.get(
        f"/prepare_info?selected_photo_ids=32812033543&cache_id={cache_id}",
    )

    assert resp.status_code == 200
    assert b"Puppy Kisses" in resp.data

    assert b"1 of 1" in resp.data

    assert "please choose your language:" in minify(resp.data)
    assert "please add a title and short caption" in minify(resp.data)


def test_renders_form_for_multiple_photo(
    logged_in_client: FlaskClient, vcr_cassette: str
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

    assert "please choose your language:" in minify(resp.data)
    assert "please add titles and captions for each photo" in minify(resp.data)


def test_blocks_uploads_with_an_invalid_title(
    logged_in_client: FlaskClient, vcr_cassette: str
) -> None:
    cache_id = get_single_photo_cache_id()

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
    logged_in_client: FlaskClient, vcr_cassette: str
) -> None:
    cache_id = get_single_photo_cache_id()

    resp = logged_in_client.post(
        f"/prepare_info?selected_photo_ids=32812033543&cache_id={cache_id}",
        data={
            "photo_32812033543-title": "A photo with a reasonable title",
            "photo_32812033543-short_caption": "A photo with a very long caption" * 100,
            "photo_32812033543-categories": "",
        },
    )

    assert resp.status_code == 200


def get_upload_requests_from_wait_for_upload_resp(
    resp: TestResponse,
) -> list[UploadRequest]:
    """
    Given a successful POST response to /prepare_info, return the list
    of upload requests created as part of the new task.
    """
    # If the task is created successfully, we should be redirected to
    # the "wait for upload" screen, which has a URL something like:
    #
    #     /wait_for_upload/ebe113ed-8c65-42b0-961b-71472064b2e0
    #
    assert resp.status_code == 302
    assert resp.headers["location"].startswith("/wait_for_upload/")

    task_id = resp.headers["location"].split("/")[2]

    # Now retrieve the task from the uploads queue, and check it was
    # created correctly.
    queue = uploads_queue()
    task = queue.read_task(task_id=task_id)

    assert task["state"] == "waiting"
    assert len(task["task_input"]["requests"]) == 1

    return task["task_input"]["requests"]


def test_creates_upload_task_for_successful_form_post(
    logged_in_client: FlaskClient, vcr_cassette: str
) -> None:
    get_photos_data = get_typed_fixture(
        path="flickr_api/single_photo-32812033543.json", model=SinglePhotoData
    )

    cache_id = save_cached_photos_data(get_photos_data)

    resp = logged_in_client.post(
        f"/prepare_info?selected_photo_ids=32812033543&cache_id={cache_id}",
        data={
            "js_enabled": "false",
            "no_js_language": "en",
            "photo_32812033543-title": "A photo with a reasonable title",
            "photo_32812033543-short_caption": "A photo with an appropriate-length caption",
            "photo_32812033543-categories": "Fish\nCats\nAnimals",
        },
    )

    upload_requests = get_upload_requests_from_wait_for_upload_resp(resp)
    assert len(upload_requests) == 1

    this_upload_request = upload_requests[0]

    assert this_upload_request["categories"] == ["Fish", "Cats", "Animals"]

    assert this_upload_request["caption"] == {
        "language": "en",
        "text": "A photo with an " "appropriate-length caption",
    }

    assert this_upload_request["photo"] == get_photos_data["photos"][0]

    assert this_upload_request["title"] == "A photo with a reasonable title.jpg"


class TestLanguageSelection:
    def get_language_from_form_submission(
        self, logged_in_client: FlaskClient, language_data: dict[str, str]
    ) -> list[UploadRequest]:
        cache_id = get_single_photo_cache_id()

        resp = logged_in_client.post(
            f"/prepare_info?selected_photo_ids=32812033543&cache_id={cache_id}",
            data={
                **language_data,
                "photo_32812033543-title": "A photo with a reasonable title",
                "photo_32812033543-short_caption": "A photo with an appropriate-length caption",
                "photo_32812033543-categories": "",
            },
        )

        return get_upload_requests_from_wait_for_upload_resp(resp)

    def test_gets_no_js_language(
        self, logged_in_client: FlaskClient, vcr_cassette: str
    ) -> None:
        upload_requests = self.get_language_from_form_submission(
            logged_in_client,
            {
                "js_enabled": "false",
                "no_js_language": "de",
                "js_language": "",
            },
        )

        assert len(upload_requests) == 1
        assert upload_requests[0]["caption"]["language"] == "de"

    @pytest.mark.parametrize("js_enabled", ["true", "false"])
    def test_blocks_empty_language(
        self,
        logged_in_client: FlaskClient,
        app: Flask,
        vcr_cassette: str,
        js_enabled: str,
    ) -> None:
        cache_id = get_single_photo_cache_id()

        resp = logged_in_client.post(
            f"/prepare_info?selected_photo_ids=32812033543&cache_id={cache_id}",
            data={
                "js_enabled": js_enabled,
                "no_js_language": "",
                "js_language": "",
                "photo_32812033543-title": "A photo with a reasonable title",
                "photo_32812033543-short_caption": "A photo with an appropriate-length caption",
                "photo_32812033543-categories": "",
            },
        )

        assert resp.status_code != 302

    def test_gets_js_language(
        self, logged_in_client: FlaskClient, vcr_cassette: str
    ) -> None:
        upload_requests = self.get_language_from_form_submission(
            logged_in_client,
            {
                "js_enabled": "true",
                "no_js_language": "",
                "js_language": '{"id":"es","label":"español","match_text":null}',
            },
        )
        assert len(upload_requests) == 1
        assert upload_requests[0]["caption"]["language"] == "es"


@pytest.mark.parametrize(
    ["original", "truncated"],
    [
        # A description which is split across many lines
        ("1\n2\n3\n4\n5\n6\n7\n", {"text": "1\n2\n3\n4", "truncated": True}),
        # A description which is split across many lines, and where even
        # the first five lines need truncating.
        (
            ("abcdefghi " * 110 + "\n") * 10,
            {"text": "abcdefghi " * 14 + "abcdefghi", "truncated": True},
        ),
        # A description which is short enough to be returned unmodified
        (
            "A blue train in a green field",
            {"text": "A blue train in a green field", "truncated": False},
        ),
        # A description which is around the target length
        ("a" * 121, {"text": "a" * 121, "truncated": False}),
        ("a" * 130, {"text": "a" * 130, "truncated": False}),
        # A description which is comfortably over the target length, truncated
        # at the right word.
        (
            "a" * 110 + " and now we have some words to push us towards the end",
            {
                "text": "a" * 110 + " and now we have some words to push us",
                "truncated": True,
            },
        ),
        # A description which is comfortably over the target length, truncated
        # just before a line break.
        (
            "a" * 115 + " and now we have\nsome words to push us towards the end",
            {"text": "a" * 115 + " and now we have", "truncated": True},
        ),
        # A description which is comfortably over the target length, truncated
        # well after a line break.
        (
            "a" * 110 + " and now we have\nsome words to push us towards the end",
            {
                "text": "a" * 110 + " and now we have\nsome words to push us",
                "truncated": True,
            },
        ),
    ],
)
def test_truncate_description(original: str, truncated: TruncationResult) -> None:
    assert truncate_description(original) == truncated


def test_escapes_html_in_description(logged_in_client: FlaskClient) -> None:
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
