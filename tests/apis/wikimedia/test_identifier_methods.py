import pytest

from flickypedia.apis import MissingFileException, WikimediaApi


def test_filename_to_id(wikimedia_api: WikimediaApi) -> None:
    assert (
        wikimedia_api.filename_to_id(filename="File:Herestraat Groningen.JPG") == "128"
    )


def test_filename_to_id_if_no_file(wikimedia_api: WikimediaApi) -> None:
    with pytest.raises(MissingFileException):
        wikimedia_api.filename_to_id(filename="File:DefinitelyDoesNotExist.jpg")


def test_id_to_filename(wikimedia_api: WikimediaApi) -> None:
    assert wikimedia_api.id_to_filename(pageid="128") == "File:Herestraat Groningen.JPG"


def test_id_to_filename_if_no_file(wikimedia_api: WikimediaApi) -> None:
    with pytest.raises(MissingFileException):
        wikimedia_api.id_to_filename(pageid="123456789123456789")
