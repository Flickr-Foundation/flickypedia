import pytest

from flickypedia.apis import MissingFileException, WikimediaApi, UnknownWikimediaApiException


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
