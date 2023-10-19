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

    assert resp.status_code == 302
    assert resp.headers["location"] == "/"
