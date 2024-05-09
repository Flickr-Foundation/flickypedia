import pytest

from flickypedia.apis import (
    DuplicateFilenameUploadException,
    DuplicatePhotoUploadException,
    WikimediaApi,
    UnknownWikimediaApiException,
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
