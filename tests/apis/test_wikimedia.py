import typing

from authlib.integrations.httpx_client import OAuth2Client
from authlib.oauth2.rfc6749.wrappers import OAuth2Token
import pytest

from flickypedia.apis.wikimedia import (
    WikimediaApi,
    InvalidAccessTokenException,
    MissingFileException,
)


@pytest.mark.parametrize(
    ["method_name", "kwargs"],
    [
        ("get_userinfo", {}),
        (
            "add_file_caption",
            {
                "filename": "GwrFireBuckets.jpg",
                "caption": {
                    "language": "en",
                    "text": "A row of red fire buckets on a heritage railway in Gloucestershire",
                },
            },
        ),
    ],
)
def test_call_api_with_bad_token(
    vcr_cassette: str, method_name: str, kwargs: dict[str, typing.Any]
) -> None:
    client = OAuth2Client(
        token=OAuth2Token(
            {
                "token_type": "Bearer",
                "expires_in": 14400,
                "access_token": "ACCESS_TOKEN",
                "refresh_token": "REFRESH_TOKEN",
            }
        ),
    )

    broken_api = WikimediaApi(client)

    with pytest.raises(InvalidAccessTokenException):
        getattr(broken_api, method_name)(**kwargs)


def test_can_get_a_csrf_token(wikimedia_api: WikimediaApi) -> None:
    assert (
        wikimedia_api.get_csrf_token() == "b06523b8444d39f30df59c8bdee0515b65253321+\\"
    )


def test_find_matching_languages(wikimedia_api: WikimediaApi) -> None:
    actual = wikimedia_api.find_matching_languages(query="des")
    expected = [
        {"id": "da", "label": "dansk", "match_text": "dens"},
        {
            "id": "ase",
            "label": "American sign language",
            "match_text": "des — langue des signes américaine",
        },
    ]

    assert actual == expected


def test_handles_no_matching_languages(wikimedia_api: WikimediaApi) -> None:
    assert wikimedia_api.find_matching_languages(query="ymr") == []


def test_get_file_without_structured_data_is_empty(wikimedia_api: WikimediaApi) -> None:
    """
    If a file exists on Commons but it doesn't have any structured data,
    we should get an empty dict back.
    """
    assert wikimedia_api.get_structured_data(filename="Nyungw.jpg") == {}


def test_get_structured_data_for_missing_file(wikimedia_api: WikimediaApi) -> None:
    with pytest.raises(MissingFileException):
        wikimedia_api.get_structured_data(filename="DefinitelyDoesNotExist.jpg")
