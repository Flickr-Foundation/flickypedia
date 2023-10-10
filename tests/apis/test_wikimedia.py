import pytest

from flickypedia.apis.wikimedia import (
    WikimediaApi,
    InvalidAccessTokenException,
    DuplicatePhotoUploadException,
    UnknownWikimediaApiException,
)


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
def test_call_api_with_bad_token(vcr_cassette, method_name, kwargs):
    broken_api = WikimediaApi(access_token="not_a_real_token")

    with pytest.raises(InvalidAccessTokenException):
        getattr(broken_api, method_name)(**kwargs)


def test_can_get_a_csrf_token(wikimedia_api):
    assert (
        wikimedia_api.get_csrf_token() == "b06523b8444d39f30df59c8bdee0515b65253321+\\"
    )


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
        with pytest.raises(
            UnknownWikimediaApiException,
        ) as exc:
            wikimedia_api.add_file_caption(
                filename="!!!.jpg",
                language="en",
                value="A file that doesn't actually exist in Wiki Commons",
            )

        assert exc.value.code == "no-such-entity-link"


def test_fails_if_uploading_image_from_disallowed_domain(wikimedia_api):
    with pytest.raises(
        UnknownWikimediaApiException,
        match="Uploads by URL are not allowed from this domain",
    ):
        wikimedia_api.upload_photo(
            photo_url="https://alexwlchan.net/images/example.jpg",
            filename="example.jpg",
            license="cc-by-2.0",
            short_caption="An image which doesn’t exist",
        )


def test_fails_if_uploading_image_which_is_duplicate(wikimedia_api):
    with pytest.raises(DuplicatePhotoUploadException):
        wikimedia_api.upload_photo(
            photo_url="https://live.staticflickr.com/65535/53248279408_c23cba9eb8_o_d.jpg",
            filename="RailwayMuseumClocks.jpg",
            license="cc-by-2.0",
            short_caption="A wall of railway pendulum clocks at the Slovenian Railway Museum in Ljubljana",
        )
