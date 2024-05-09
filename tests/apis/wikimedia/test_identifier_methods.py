import pytest

from flickypedia.apis import MissingFileException, WikimediaApi


class TestIdentifierMethods:
    def test_filename_to_pageid(self, wikimedia_api: WikimediaApi) -> None:
        assert (
            wikimedia_api.filename_to_pageid(filename="File:Herestraat Groningen.JPG")
            == "128"
        )

    def test_filename_to_pageid_if_no_file(self, wikimedia_api: WikimediaApi) -> None:
        with pytest.raises(MissingFileException):
            wikimedia_api.filename_to_pageid(filename="File:DefinitelyDoesNotExist.jpg")

    def test_pageid_to_filename(self, wikimedia_api: WikimediaApi) -> None:
        assert (
            wikimedia_api.pageid_to_filename(pageid="128")
            == "File:Herestraat Groningen.JPG"
        )

    def test_pageid_to_filename_if_no_file(self, wikimedia_api: WikimediaApi) -> None:
        with pytest.raises(MissingFileException):
            wikimedia_api.pageid_to_filename(pageid="123456789123456789")
