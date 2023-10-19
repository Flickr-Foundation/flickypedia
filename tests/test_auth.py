def test_oauth2_authorize_wikimedia_redirects_you(app):
    app.config["OAUTH2_PROVIDERS"]["wikimedia"]["client_id"] = "example1234"

    with app.test_client() as client:
        resp = client.get("/authorize/wikimedia")

    assert resp.status_code == 302
    assert (
        resp.headers["location"]
        == "https://meta.wikimedia.org/w/rest.php/oauth2/authorize?client_id=example1234&response_type=code"
    )


def test_if_logged_in_authorize_redirects_to_homepage(logged_in_client):
    resp = logged_in_client.get("/authorize/wikimedia")

    # If you're already logged in, you should be redirected to the homepage
    assert resp.status_code == 302
    assert resp.headers["location"] == "/"


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
