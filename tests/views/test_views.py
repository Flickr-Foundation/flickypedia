import json


def test_can_load_about_page(client):
    resp = client.get("/about/")

    assert b"<h2>About Flickypedia</h2>" in resp.data


def test_can_load_bookmarklet(client):
    resp = client.get("/bookmarklet/")

    assert b"<h2>Flickypedia bookmarklet</h2>" in resp.data


class TestValidateTitleApi:
    def test_not_logged_in_is_error(self, client):
        resp = client.get("/api/validate_title?title=File:apple.jpg")

        assert resp.status_code == 302
        assert (
            resp.headers["location"]
            == "/?next=%2Fapi%2Fvalidate_title%3Ftitle%3DFile%3Aapple.jpg"
        )

    def test_missing_title_param_is_error(self, logged_in_client):
        resp = logged_in_client.get("/api/validate_title")

        assert resp.status_code == 400

    def test_title_without_file_prefix_is_error(self, logged_in_client):
        resp = logged_in_client.get("/api/validate_title?title=apple")

        assert resp.status_code == 400

    def test_gets_title_validation(self, logged_in_client, vcr_cassette):
        resp = logged_in_client.get("/api/validate_title?title=File:apple.jpg")

        assert resp.status_code == 200
        assert json.loads(resp.data)["result"] == "duplicate"
