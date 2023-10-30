class TestOAuth2AuthorizeWikimedia:
    def test_new_user_is_redirected_to_wikimedia(self, app):
        app.config["OAUTH2_PROVIDERS"]["wikimedia"]["client_id"] = "example1234"

        with app.test_client() as client:
            resp = client.get("/authorize/wikimedia")

        assert resp.status_code == 302
        assert (
            resp.headers["location"]
            == "https://meta.wikimedia.org/w/rest.php/oauth2/authorize?client_id=example1234&response_type=code"
        )

    def test_logged_in_user_is_redirected_to_get_photos(self, logged_in_client):
        resp = logged_in_client.get("/authorize/wikimedia")

        # If you're already logged in, you should be redirected
        assert resp.status_code == 302
        assert resp.headers["location"] == "/get_photos"


def test_logging_out_removes_user(logged_in_client):
    logout_resp = logged_in_client.get("/logout")

    # After you're logged out, you should be redirected to the homepage
    assert logout_resp.status_code == 302
    assert logout_resp.headers["location"] == "/"

    # After you've logged out, trying to re-authorize with Wikimedia
    # should send you off to their auth screen rather than straight
    # back into Flickypedia.
    auth_resp = logged_in_client.get("/authorize/wikimedia")
    assert auth_resp.headers["location"].startswith("https://meta.wikimedia.org/")


class TestOAuth2CallbackWikimedia:
    def test_already_logged_in_bypasses_flow(self, logged_in_client):
        resp = logged_in_client.get("/callback/wikimedia")

        # If you're already logged in, you don't need to come through
        # this flow.
        assert resp.status_code == 302
        assert resp.headers["location"] == "/get_photos"

    def test_missing_code_is_error(self, client):
        resp = client.get("/callback/wikimedia")

        assert resp.status_code == 401

    def test_bad_token_from_wikimedia_is_error(self, app, vcr_cassette):
        app.config["OAUTH2_PROVIDERS"]["wikimedia"].update(
            {
                "client_id": "client1234",
                "client_secret": "client1234",
            }
        )

        with app.test_client() as client:
            resp = client.get("/callback/wikimedia?code=123")

        assert resp.status_code == 401
