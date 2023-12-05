import json

from flask.testing import FlaskClient


class TestValidateTitleApi:
    def test_not_logged_in_is_error(self, client: FlaskClient) -> None:
        resp = client.get("/api/validate_title?title=File:apple.jpg")

        assert resp.status_code == 302
        assert (
            resp.headers["location"]
            == "/?next=%2Fapi%2Fvalidate_title%3Ftitle%3DFile%3Aapple.jpg"
        )

    def test_missing_title_param_is_error(self, logged_in_client: FlaskClient) -> None:
        resp = logged_in_client.get("/api/validate_title")

        assert resp.status_code == 400

    def test_title_without_file_prefix_is_error(
        self, logged_in_client: FlaskClient
    ) -> None:
        resp = logged_in_client.get("/api/validate_title?title=apple")

        assert resp.status_code == 400

    def test_gets_title_validation(
        self, logged_in_client: FlaskClient, vcr_cassette: str
    ) -> None:
        resp = logged_in_client.get("/api/validate_title?title=File:apple.jpg")

        assert resp.status_code == 200
        assert json.loads(resp.data)["result"] == "duplicate"


class TestFindMatchingCategoriesApi:
    def test_not_logged_in_is_error(self, client: FlaskClient) -> None:
        resp = client.get("/api/find_matching_categories?query=apple")

        assert resp.status_code == 302
        assert (
            resp.headers["location"]
            == "/?next=%2Fapi%2Ffind_matching_categories%3Fquery%3Dapple"
        )

    def test_missing_query_param_is_error(self, logged_in_client: FlaskClient) -> None:
        resp = logged_in_client.get("/api/find_matching_categories")

        assert resp.status_code == 400

    def test_empty_query_param_is_error(self, logged_in_client: FlaskClient) -> None:
        resp = logged_in_client.get("/api/find_matching_categories?query=")

        assert resp.status_code == 400

    def test_finds_matching_categories(
        self, logged_in_client: FlaskClient, vcr_cassette: str
    ) -> None:
        resp = logged_in_client.get("/api/find_matching_categories?query=apple")

        assert resp.status_code == 200
        assert json.loads(resp.data) == [
            "Apple",
            "Appleton, Wisconsin",
            "Apples",
            "Apple trees in Germany",
            "Apples of the Hesperides",
            "Apple trees",
            "Apple trees in Russia",
            "Apple trees in Lithuania",
            "Apple trees in Turkey",
            "Apple trees in Armenia",
        ]


class TestFindMatchingLanguagesApi:
    def test_not_logged_in_is_error(self, client: FlaskClient) -> None:
        resp = client.get("/api/find_matching_languages?query=eng")

        assert resp.status_code == 302
        assert (
            resp.headers["location"]
            == "/?next=%2Fapi%2Ffind_matching_languages%3Fquery%3Deng"
        )

    def test_returns_top_10_languages_if_no_query(
        self, logged_in_client: FlaskClient
    ) -> None:
        resp = logged_in_client.get("/api/find_matching_languages")

        assert resp.status_code == 200
        assert json.loads(resp.data) == [
            {"id": "en", "label": "English", "match_text": None},
            {"id": "de", "label": "Deutsch", "match_text": None},
            {"id": "fr", "label": "français", "match_text": None},
            {"id": "ru", "label": "русский", "match_text": None},
            {"id": "es", "label": "español", "match_text": None},
            {"id": "nl", "label": "Nederlands", "match_text": None},
            {"id": "it", "label": "italiano", "match_text": None},
            {"id": "ar", "label": "العربية", "match_text": None},
            {"id": "pl", "label": "polski", "match_text": None},
            {"id": "fa", "label": "فارسی", "match_text": None},
        ]

    def test_returns_languages_matching_query(
        self, logged_in_client: FlaskClient, vcr_cassette: str
    ) -> None:
        resp = logged_in_client.get("/api/find_matching_languages?query=ger")

        assert resp.status_code == 200
        assert json.loads(resp.data) == [
            {"id": "de", "label": "Deutsch", "match_text": "german"},
            {"id": "el", "label": "Ελληνικά", "match_text": "gereg"},
            {
                "id": "de-at",
                "label": "Österreichisches Deutsch",
                "match_text": "germana aŭstra",
            },
            {
                "id": "de-ch",
                "label": "Schweizer Hochdeutsch",
                "match_text": "germana svisa",
            },
            {
                "id": "de-formal",
                "label": "Deutsch (Sie-Form)",
                "match_text": "german (formal address)",
            },
            {
                "id": "pdc",
                "label": "Deitsch",
                "match_text": "german — pennsylvania german",
            },
            {"id": "gsw", "label": "Alemannisch", "match_text": "german swiss"},
            {"id": "nds", "label": "Plattdüütsch", "match_text": "germana de jos"},
            {"id": "grc", "label": "Ἀρχαία ἑλληνικὴ", "match_text": "geregu arkaiku"},
            {
                "id": "cu",
                "label": "словѣньскъ / ⰔⰎⰑⰂⰡⰐⰠⰔⰍⰟ",
                "match_text": "gereja — bahasa gereja slavonia",
            },
            {
                "id": "nds-nl",
                "label": "Nedersaksies",
                "match_text": "german — west low german",
            },
            {"id": "hz", "label": "Otsiherero", "match_text": "gerero"},
            {
                "id": "pfl",
                "label": "Pälzisch",
                "match_text": "german — palatine german",
            },
        ]
