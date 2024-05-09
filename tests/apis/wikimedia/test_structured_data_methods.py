import pytest

from flickypedia.apis.structured_data import create_license_statement
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
            summary="Flickypedia edit (add structured data statements)",
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
                summary="Flickypedia edit (add structured data statements)",
            )

        assert exc.value.code == "no-such-entity-link"

    def test_throws_error_for_bad_sdc_format(self, wikimedia_api: WikimediaApi) -> None:
        with pytest.raises(TypeError):
            wikimedia_api.add_structured_data(
                filename="example.jpg",
                data=[create_license_statement(license_id="cc-by-2.0")],  # type: ignore
                summary="Flickypedia edit (add structured data statements)",
            )
