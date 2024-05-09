import typing

from authlib.integrations.httpx_client import OAuth2Client
from authlib.oauth2.rfc6749.wrappers import OAuth2Token
import pytest

from flickypedia.apis.wikimedia import (
    WikimediaApi,
    DuplicateFilenameUploadException,
    DuplicatePhotoUploadException,
    InvalidAccessTokenException,
    MissingFileException,
    UnknownWikimediaApiException,
)


def test_get_userinfo(wikimedia_api: WikimediaApi) -> None:
    info = wikimedia_api.get_userinfo()

    assert info == {"id": 829939, "name": "Alexwlchan"}


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


class TestUploadImage:
    def test_can_upload_an_image(self, wikimedia_api: WikimediaApi) -> None:
        text = "=={{int:filedesc}}==\n{{Information}}\n\n=={{int:license-header}}==\n{{cc-by-2.0}}\n"

        resp = wikimedia_api.upload_image(
            filename="Silver Blue Fish In Boston Aquarium.jpg",
            original_url="https://live.staticflickr.com/8338/8273352482_50cb58a54f_o_d.jpg",
            text=text,
        )

        assert resp == "Silver_Blue_Fish_In_Boston_Aquarium.jpg"

    def test_fails_if_uploading_image_from_disallowed_domain(
        self, wikimedia_api: WikimediaApi
    ) -> None:
        with pytest.raises(
            UnknownWikimediaApiException,
            match="Uploads by URL are not allowed from this domain",
        ):
            wikimedia_api.upload_image(
                filename="example.jpg",
                original_url="https://alexwlchan.net/images/example.jpg",
                text="An image which doesn’t even exist",
            )

    def test_fails_if_uploading_non_existent_image(
        self, wikimedia_api: WikimediaApi
    ) -> None:
        with pytest.raises(
            UnknownWikimediaApiException,
            match="Uploads by URL are not allowed from this domain",
        ):
            wikimedia_api.upload_image(
                filename="example.jpg",
                original_url="https://flickr.com/doesntexist.jpg",
                text="An image which doesn’t even exist",
            )

    def test_fails_if_uploading_image_which_is_duplicate(
        self, wikimedia_api: WikimediaApi
    ) -> None:
        with pytest.raises(DuplicateFilenameUploadException) as exc:
            wikimedia_api.upload_image(
                filename="RailwayMuseumClocks.jpg",
                original_url="https://live.staticflickr.com/65535/53248279408_c23cba9eb8_o_d.jpg",
                text="A wall of railway pendulum clocks at the Slovenian Railway Museum in Ljubljana",
            )

        assert exc.value.filename == "RailwayMuseumClocks.jpg"

    def test_fails_if_uploading_image_which_is_duplicate_hash(
        self, wikimedia_api: WikimediaApi
    ) -> None:
        with pytest.raises(DuplicatePhotoUploadException) as exc:
            wikimedia_api.upload_image(
                filename="Yellow fish at Houston Zoo aquarium.jpg",
                original_url="https://live.staticflickr.com/6192/6054362864_a8f52ef695_o_d.jpg",
                text="A yellow fish",
            )

        assert exc.value.filename == "Yellow_Fin_(6054362864).jpg"


@pytest.mark.parametrize(
    ["title", "result"],
    [
        pytest.param(
            "File:StainedGlassWindowAtEly.jpg",
            "duplicate",
            id="duplicate_title",
        ),
        pytest.param("File:P60506151.jpg", "blacklisted", id="blacklisted_title"),
        pytest.param(
            "File:" + "a" * 241 + ".tiff",
            "too_long",
            id="barely_too_long_title",
        ),
        pytest.param(f"File:{'Fishing' * 100}.jpg", "too_long", id="too_long_title"),
        pytest.param(
            "File:{with invalid chars}.jpg",
            "invalid",
            id="disallowed_characters",
        ),
        pytest.param("File:\b\b\b.jpg", "invalid", id="disallowed_characters_2"),
        pytest.param("File:.", "invalid", id="only_a_single_period"),
        pytest.param("File:FishingBoatsByTheRiver.jpg", "ok", id="allowed_title"),
        pytest.param("File:FishingBoatsByTheRiver.jpg", "ok", id="allowed_title"),
    ],
)
def test_validate_title(wikimedia_api: WikimediaApi, title: str, result: str) -> None:
    assert wikimedia_api.validate_title(title=title)["result"] == result


def test_validate_title_links_to_duplicates(wikimedia_api: WikimediaApi) -> None:
    result = wikimedia_api.validate_title(title="File:P1.jpg")

    assert result == {
        "result": "duplicate",
        "text": "Please choose a different title. There is already <a href='https://commons.wikimedia.org/wiki/File:P1.jpg'>a file on Commons</a> with that title.",
    }


def test_validate_title_links_to_normalised_duplicates(
    wikimedia_api: WikimediaApi,
) -> None:
    result = wikimedia_api.validate_title(title="File:Tower Bridge at Night.jpg")

    assert result == {
        "result": "duplicate",
        "text": "Please choose a different title. There is already a file <a href='https://commons.wikimedia.org/wiki/File:Tower Bridge at Night.JPG'>Tower Bridge at Night.JPG</a> on Commons.",
    }


def test_validate_title_links_to_case_insensitive_duplicates(
    wikimedia_api: WikimediaApi,
) -> None:
    result = wikimedia_api.validate_title(title="File:tower bridge at night.jpg")

    assert result == {
        "result": "duplicate",
        "text": "Please choose a different title. There is already a file <a href='https://commons.wikimedia.org/wiki/File:Tower Bridge at Night.JPG'>Tower Bridge at Night.JPG</a> on Commons.",
    }


@pytest.mark.parametrize(
    "title",
    [
        "Belgian President in 2023.jpg",
        "Jam on a slice of bread.png",
        "A shipping container full of bees.JPEG",
    ],
)
def test_validate_title_rejects_image_suffix(
    wikimedia_api: WikimediaApi, title: str
) -> None:
    result = wikimedia_api.validate_title(title=f"File:{title}.jpg")

    assert result == {
        "result": "invalid",
        "text": "Please remove the filename suffix; it will be added automatically.",
    }


@pytest.mark.parametrize(
    "title", ["This:is:a:title:with:colons", "This/is\\a/title\\with/slashes"]
)
def test_validate_title_rejects_illegal_chars(
    wikimedia_api: WikimediaApi, title: str
) -> None:
    result = wikimedia_api.validate_title(title=f"File:{title}.jpg")

    assert result == {
        "result": "invalid",
        "text": "This title is invalid. Make sure to remove characters like square brackets, colons, slashes, comparison operators, pipes and curly brackets.",
    }


def test_find_matching_categories(wikimedia_api: WikimediaApi) -> None:
    result = wikimedia_api.find_matching_categories(query="a")

    assert result == [
        "A",
        "Amsterdam in the 1810s",
        "Aircraft of Uzbekistan",
        "Aircraft registered in Mali",
        "Architectural elements in Germany",
        "Aircraft in Portugal",
        "Aircraft in Sierra Leone",
        "Aircraft in Malawi",
        "Aircraft in Tanzanian service",
        "Aircraft in Thailand",
    ]


def test_can_find_rare_categories(wikimedia_api: WikimediaApi) -> None:
    result = wikimedia_api.find_matching_categories(query="Aircraft in Taj")

    assert result == [
        "Aircraft in Tajikistan",
        "Aircraft in Tajikistani service",
        "Aircraft in Tajikistani service by airline",
    ]


def test_returns_an_empty_list_if_no_matching_categories(
    wikimedia_api: WikimediaApi,
) -> None:
    assert wikimedia_api.find_matching_categories(query="sdfdsgd") == []


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


def test_get_wikitext(wikimedia_api: WikimediaApi) -> None:
    actual = wikimedia_api.get_wikitext(
        filename="File:The main Flickr photo storage server.jpg"
    )

    with open(
        "tests/fixtures/wikitext/The_main_Flickr_photo_storage_server.html"
    ) as infile:
        expected = infile.read()

    assert actual == expected


def test_get_wikitext_for_missing_file(wikimedia_api: WikimediaApi) -> None:
    with pytest.raises(MissingFileException):
        wikimedia_api.get_wikitext(filename="File:DefinitelyDoesNotExist.jpg")


def test_bad_filename_is_exception(wikimedia_api: WikimediaApi) -> None:
    with pytest.raises(UnknownWikimediaApiException):
        wikimedia_api.get_wikitext(filename="File:")


def test_get_file_without_structured_data_is_empty(wikimedia_api: WikimediaApi) -> None:
    """
    If a file exists on Commons but it doesn't have any structured data,
    we should get an empty dict back.
    """
    assert wikimedia_api.get_structured_data(filename="Nyungw.jpg") == {}


def test_get_structured_data_for_missing_file(wikimedia_api: WikimediaApi) -> None:
    with pytest.raises(MissingFileException):
        wikimedia_api.get_structured_data(filename="DefinitelyDoesNotExist.jpg")
