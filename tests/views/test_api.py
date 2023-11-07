import json

from flask import FlaskClient


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
