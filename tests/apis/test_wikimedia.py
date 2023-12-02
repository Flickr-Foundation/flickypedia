from typing import Any

from authlib.integrations.httpx_client.oauth2_client import OAuth2Client
from authlib.oauth2.rfc6749.wrappers import OAuth2Token
import pytest

from flickypedia.apis.structured_data import create_license_statement
from flickypedia.apis.wikimedia import (
    WikimediaApi,
    DuplicateFilenameUploadException,
    DuplicatePhotoUploadException,
    InvalidAccessTokenException,
    UnknownWikimediaApiException,
)
from flickypedia.apis.wikitext import create_wikitext


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
    vcr_cassette: str, method_name: str, kwargs: dict[str, Any]
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
    # def test_can_upload_an_image(self, wikimedia_api: WikimediaApi) -> None:
    #     text = create_wikitext(license_id="cc-by-2.0", new_categories=[])
    #
    #     resp = wikimedia_api.upload_image(
    #         filename="Silver Blue Fish In Boston Aquarium.jpg",
    #         original_url="https://live.staticflickr.com/8338/8273352482_50cb58a54f_o_d.jpg",
    #         text=text,
    #     )
    #
    #     assert resp == "Silver_Blue_Fish_In_Boston_Aquarium.jpg"

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


class TestAddFileCaption:
    def test_can_set_a_file_caption(self, wikimedia_api: WikimediaApi) -> None:
        wikimedia_api.add_file_caption(
            filename="GwrFireBuckets.jpg",
            caption={
                "language": "en",
                "text": "A row of red fire buckets on a heritage railway in Gloucestershire",
            },
        )

    def test_fails_if_file_caption_is_too_long(
        self, wikimedia_api: WikimediaApi
    ) -> None:
        # The maximum length of a file caption is ~250 characters, so
        # this will easily be too long.
        with pytest.raises(UnknownWikimediaApiException) as exc:
            wikimedia_api.add_file_caption(
                filename="GwrFireBuckets.jpg",
                caption={
                    "language": "en",
                    "text": "A row of red fire buckets on a heritage railway in Gloucestershire"
                    * 10,
                },
            )

        assert exc.value.code == "modification-failed"

    def test_fails_if_bad_language(self, wikimedia_api: WikimediaApi) -> None:
        with pytest.raises(UnknownWikimediaApiException) as exc:
            wikimedia_api.add_file_caption(
                filename="GwrFireBuckets.jpg",
                caption={
                    "language": "doesnotexist",
                    "text": "A row of red fire buckets on a heritage railway in Gloucestershire",
                },
            )

        assert exc.value.code == "badvalue"

    def test_fails_if_file_does_not_exist(self, wikimedia_api: WikimediaApi) -> None:
        with pytest.raises(UnknownWikimediaApiException) as exc:
            wikimedia_api.add_file_caption(
                filename="!!!.jpg",
                caption={
                    "language": "en",
                    "text": "A file that doesn't actually exist in Wiki Commons",
                },
            )

        assert exc.value.code == "no-such-entity-link"


class TestAddStructuredData:
    def test_can_add_structured_data(self, wikimedia_api: WikimediaApi) -> None:
        # This test was run against one of my Wikimedia Commons images
        # which didn't have any SDC attached; I added the license statement
        # and checked that it was updated as part of the process.
        before_statements = wikimedia_api.get_structured_data(
            filename="PrintedLibraryOfCongressSubjectHeadings.jpg"
        )

        assert "P275" not in before_statements

        wikimedia_api.add_structured_data(
            filename="PrintedLibraryOfCongressSubjectHeadings.jpg",
            data={"claims": [create_license_statement(license_id="cc-by-2.0")]},
        )

        after_statements = wikimedia_api.get_structured_data(
            filename="PrintedLibraryOfCongressSubjectHeadings.jpg"
        )

        assert after_statements["P275"] == [
            {
                "id": "M138833893$3EDD9F54-EFDF-4D25-A431-F4A03486265D",
                "mainsnak": {
                    "datavalue": {
                        "type": "wikibase-entityid",
                        "value": {
                            "entity-type": "item",
                            "id": "Q19125117",
                            "numeric-id": 19125117,
                        },
                    },
                    "hash": "82d5b402aa0a79040483a8c9264bd484c6c13f67",
                    "property": "P275",
                    "snaktype": "value",
                },
                "rank": "normal",
                "type": "statement",
            }
        ]

    def test_fails_sdc_if_file_does_not_exist(
        self, wikimedia_api: WikimediaApi
    ) -> None:
        with pytest.raises(UnknownWikimediaApiException) as exc:
            wikimedia_api.add_structured_data(
                filename="!!!.jpg",
                data={"claims": [create_license_statement(license_id="cc-by-2.0")]},
            )

        assert exc.value.code == "no-such-entity-link"

    def test_throws_error_for_bad_sdc_format(self, wikimedia_api: WikimediaApi) -> None:
        with pytest.raises(TypeError):
            wikimedia_api.add_structured_data(
                filename="example.jpg",
                data=[create_license_statement(license_id="cc-by-2.0")],  # type: ignore
            )


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
