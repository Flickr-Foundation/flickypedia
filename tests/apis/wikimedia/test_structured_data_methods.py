import pytest

from flickypedia.apis import UnknownWikimediaApiException, WikimediaApi


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
