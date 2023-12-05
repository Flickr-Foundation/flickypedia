from collections.abc import Generator
import json

from authlib.integrations.httpx_client import OAuth1Client
import keyring
import pytest
import vcr

from flickypedia.apis.flickr import (
    FlickrApiException,
    FlickrCommentsApi,
    InsufficientPermissionsToComment,
    ResourceNotFound,
    create_bot_comment_text,
)


@pytest.fixture(scope="function")
def flickr_comments_api(
    cassette_name: str, user_agent: str
) -> Generator[FlickrCommentsApi, None, None]:
    """
    Creates an instance of the FlickrCommentsApi class for use in tests.

    This instance of the API will record its interactions as "cassettes"
    using vcr.py, which can be replayed offline (e.g. in CI tests).
    """
    with vcr.use_cassette(
        cassette_name,
        cassette_library_dir="tests/fixtures/cassettes",
    ):
        stored_token = json.loads(
            keyring.get_password("flickypedia.bot", "oauth_token") or "{}"
        )

        client = OAuth1Client(
            client_id=keyring.get_password("flickypedia", "api_key") or "123",
            client_secret=keyring.get_password("flickypedia", "api_secret") or "456",
            signature_type="QUERY",
            token=stored_token.get("oauth_token"),
            token_secret=stored_token.get("oauth_token_secret"),
        )

        yield FlickrCommentsApi(client)


def test_throws_if_not_allowed_to_post_comment(
    flickr_comments_api: FlickrCommentsApi,
) -> None:
    with pytest.raises(InsufficientPermissionsToComment):
        flickr_comments_api.post_comment(
            photo_id="53374767803",
            comment_text="This is a comment on a photo where I’ve disabled commenting",
        )


def test_throws_if_invalid_oauth_signature(vcr_cassette: str) -> None:
    stored_token = json.loads(
        keyring.get_password("flickypedia.bot", "oauth_token") or "{}"
    )

    client = OAuth1Client(
        client_id=keyring.get_password("flickypedia", "api_key") or "123",
        client_secret=keyring.get_password("flickypedia", "api_secret") or "456",
        signature_type="QUERY",
        token=stored_token.get("oauth_token"),
        token_secret=None,
    )

    api = FlickrCommentsApi(client)

    with pytest.raises(FlickrApiException):
        api.post_comment(
            photo_id="53374767803",
            comment_text="This is a comment that uses bogus OAuth 1.0a credentials",
        )


def test_throws_if_photo_doesnt_exist(flickr_comments_api: FlickrCommentsApi) -> None:
    with pytest.raises(ResourceNotFound):
        flickr_comments_api.post_comment(
            photo_id="-1", comment_text="This is a comment on a non-existent photo"
        )


def test_can_successfully_post_a_comment(
    flickr_comments_api: FlickrCommentsApi,
) -> None:
    comment_id = flickr_comments_api.post_comment(
        photo_id="53373661077",
        comment_text="This is a comment posted by the Flickypedia unit tests",
    )

    # Check that if we double-post, we get the same comment ID back --
    # that is, that commenting is an idempotent operation.
    comment_id2 = flickr_comments_api.post_comment(
        photo_id="53373661077",
        comment_text="This is a comment posted by the Flickypedia unit tests",
    )

    assert comment_id == comment_id2


def test_create_bot_comment_text() -> None:
    actual = create_bot_comment_text(
        user_url="https://commons.wikimedia.org/wiki/User:Alexwlchan",
        user_name="Alexwlchan",
        wikimedia_page_title="File:London_Bridge_At_Night.jpg",
    )

    expected = """Hi, I’m <a href="https://www.flickr.com/people/flickypedia">Flickypedia Bot</a>.

A Wikimedia Commons user named <a href="https://commons.wikimedia.org/wiki/User:Alexwlchan">Alexwlchan</a> has uploaded your photo to <a href="https://commons.wikimedia.org/wiki/Main_Page">Wikimedia Commons</a>.

<a href="https://commons.wikimedia.org/wiki/File:London_Bridge_At_Night.jpg">Would you like to see</a>? We hope you like it!"""

    assert actual == expected
