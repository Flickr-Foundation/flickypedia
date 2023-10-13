import pytest

from flickypedia.apis.structured_data import create_license_statement
from flickypedia.apis.wikimedia import (
    WikimediaApi,
    InvalidAccessTokenException,
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
