import pytest

from flickypedia.apis.structured_data import create_license_statement
from flickypedia.apis.wikimedia import (
    WikimediaApi,
    WikimediaPublicApi,
    DuplicateFilenameUploadException,
    DuplicatePhotoUploadException,
    InvalidAccessTokenException,
    UnknownWikimediaApiException,
    validate_title,
)
from flickypedia.apis.wikitext import create_wikitext


def test_get_userinfo(wikimedia_api):
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
                "language": "en",
                "value": "A row of red fire buckets on a heritage railway in Gloucestershire",
            },
        ),
    ],
)
def test_call_api_with_bad_token(vcr_cassette, user_agent, method_name, kwargs):
    broken_api = WikimediaApi(access_token="not_a_real_token", user_agent=user_agent)

    with pytest.raises(InvalidAccessTokenException):
        getattr(broken_api, method_name)(**kwargs)


def test_can_get_a_csrf_token(wikimedia_api):
    assert (
        wikimedia_api.get_csrf_token() == "b06523b8444d39f30df59c8bdee0515b65253321+\\"
    )


class TestUploadImage:
    def test_can_upload_an_image(self, wikimedia_api):
        text = create_wikitext(license_id="cc-by-2.0")

        resp = wikimedia_api.upload_image(
            filename="Silver Blue Fish In Boston Aquarium.jpg",
            original_url="https://live.staticflickr.com/8338/8273352482_50cb58a54f_o_d.jpg",
            text=text,
        )

        assert resp == "Silver_Blue_Fish_In_Boston_Aquarium.jpg"

    def test_fails_if_uploading_image_from_disallowed_domain(self, wikimedia_api):
        with pytest.raises(
            UnknownWikimediaApiException,
            match="Uploads by URL are not allowed from this domain",
        ):
            wikimedia_api.upload_image(
                filename="example.jpg",
                original_url="https://alexwlchan.net/images/example.jpg",
                text="An image which doesn’t even exist",
            )

    def test_fails_if_uploading_non_existent_image(self, wikimedia_api):
        with pytest.raises(
            UnknownWikimediaApiException,
            match="Uploads by URL are not allowed from this domain",
        ):
            wikimedia_api.upload_image(
                filename="example.jpg",
                original_url="https://flickr.com/doesntexist.jpg",
                text="An image which doesn’t even exist",
            )

    def test_fails_if_uploading_image_which_is_duplicate(self, wikimedia_api):
        with pytest.raises(DuplicateFilenameUploadException) as exc:
            wikimedia_api.upload_image(
                filename="RailwayMuseumClocks.jpg",
                original_url="https://live.staticflickr.com/65535/53248279408_c23cba9eb8_o_d.jpg",
                text="A wall of railway pendulum clocks at the Slovenian Railway Museum in Ljubljana",
            )

        assert exc.value.filename == "RailwayMuseumClocks.jpg"

    def test_fails_if_uploading_image_which_is_duplicate_hash(self, wikimedia_api):
        with pytest.raises(DuplicatePhotoUploadException) as exc:
            wikimedia_api.upload_image(
                filename="Yellow fish at Houston Zoo aquarium.jpg",
                original_url="https://live.staticflickr.com/6192/6054362864_a8f52ef695_o_d.jpg",
                text="A yellow fish",
            )

        assert exc.value.filename == "Yellow_Fin_(6054362864).jpg"


class TestAddFileCaption:
    def test_can_set_a_file_caption(self, wikimedia_api):
        wikimedia_api.add_file_caption(
            filename="GwrFireBuckets.jpg",
            language="en",
            value="A row of red fire buckets on a heritage railway in Gloucestershire",
        )

    def test_fails_if_file_caption_is_too_long(self, wikimedia_api):
        # The maximum length of a file caption is ~250 characters, so
        # this will easily be too long.
        with pytest.raises(UnknownWikimediaApiException) as exc:
            wikimedia_api.add_file_caption(
                filename="GwrFireBuckets.jpg",
                language="en",
                value="A row of red fire buckets on a heritage railway in Gloucestershire"
                * 10,
            )

        assert exc.value.code == "modification-failed"

    def test_fails_if_bad_language(self, wikimedia_api):
        with pytest.raises(UnknownWikimediaApiException) as exc:
            wikimedia_api.add_file_caption(
                filename="GwrFireBuckets.jpg",
                language="doesnotexist",
                value="A row of red fire buckets on a heritage railway in Gloucestershire",
            )

        assert exc.value.code == "badvalue"

    def test_fails_if_file_does_not_exist(self, wikimedia_api):
        with pytest.raises(UnknownWikimediaApiException) as exc:
            wikimedia_api.add_file_caption(
                filename="!!!.jpg",
                language="en",
                value="A file that doesn't actually exist in Wiki Commons",
            )

        assert exc.value.code == "no-such-entity-link"


class TestAddStructuredData:
    def test_can_add_structured_data(self, wikimedia_api):
        # This test was run against one of my Wikimedia Commons images
        # which didn't have any SDC attached; I added the license statement
        # and checked that it was updated as part of the process.
        before_data = wikimedia_api.get_structured_data(
            filename="PrintedLibraryOfCongressSubjectHeadings.jpg"
        )

        assert "P275" not in before_data["entities"]["M138833893"]["statements"]

        wikimedia_api.add_structured_data(
            filename="PrintedLibraryOfCongressSubjectHeadings.jpg",
            data={"claims": [create_license_statement(license_id="cc-by-2.0")]},
        )

        after_data = wikimedia_api.get_structured_data(
            filename="PrintedLibraryOfCongressSubjectHeadings.jpg"
        )

        assert after_data["entities"]["M138833893"]["statements"]["P275"] == [
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

    def test_fails_sdc_if_file_does_not_exist(self, wikimedia_api):
        with pytest.raises(UnknownWikimediaApiException) as exc:
            wikimedia_api.add_structured_data(
                filename="!!!.jpg",
                data={"claims": [create_license_statement(license_id="cc-by-2.0")]},
            )

        assert exc.value.code == "no-such-entity-link"

    def test_throws_error_for_bad_sdc_format(self, wikimedia_api):
        with pytest.raises(TypeError):
            wikimedia_api.add_structured_data(
                filename="example.jpg",
                data=[create_license_statement(license_id="cc-by-2.0")],
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
def test_validate_title(vcr_cassette, title, result):
    assert validate_title(title=title)["result"] == result
