import pathlib

from flask.testing import FlaskClient
from flask_login import FlaskLoginClient

from flickypedia.uploadr import create_app
from utils import store_user


def test_renders_basic_page(logged_in_client: FlaskClient) -> None:
    resp = logged_in_client.get("/get_photos")

    assert resp.status_code == 200
    assert b"Put your Flickr URL here" in resp.data


def test_rejects_a_non_flickr_url(logged_in_client: FlaskClient) -> None:
    resp = logged_in_client.post(
        "/get_photos", data={"flickr_url": "https://example.net"}
    )

    assert resp.status_code == 200

    assert b"Put your Flickr URL here" in resp.data
    assert "That URL doesn’t live on Flickr.com" in resp.data.decode("utf8")
    assert b'value="https://example.net"' in resp.data


def test_rejects_a_non_photo_flickr_url(logged_in_client: FlaskClient) -> None:
    resp = logged_in_client.post(
        "/get_photos", data={"flickr_url": "https://flickr.com/help"}
    )

    assert resp.status_code == 200

    assert b"Put your Flickr URL here" in resp.data
    assert b"There are no photos to show at that URL" in resp.data
    assert b'value="https://flickr.com/help"' in resp.data


def test_redirects_if_photo_url(logged_in_client: FlaskClient) -> None:
    flickr_url = "https://www.flickr.com/photos/schlesinger_library/13270291833"

    resp = logged_in_client.post("/get_photos", data={"flickr_url": flickr_url})

    assert resp.status_code == 302
    assert resp.headers["location"] == f"/select_photos?flickr_url={flickr_url}"


def test_preserves_photo_if_csrf_bad(tmp_path: pathlib.Path) -> None:
    """
    If the user submits the form after their CSRF token expires, we
    don't lose the URL they've typed in.

    I wrote this test after leaving the "select photos" screen open
    a while, entering a new URL, and clicking "GO".  I got back to
    the "find photos" screen but it had forgotten my URL.  No more!
    """
    # We have to create the app object manually, rather than using the
    # fixtures provided in ``conftest.py`` -- they disable CSRF for
    # ease of testing, but in this case we need CSRF to replicate the bug.
    app = create_app(data_directory=tmp_path)
    app.config["TESTING"] = True

    app.config["WTF_CSRF_ENABLED"] = True

    app.test_client_class = FlaskLoginClient

    with app.test_request_context():
        with app.test_client() as client:
            store_user(client)

            resp = client.post(
                "/get_photos",
                data={
                    "flickr_url": "https://www.flickr.com/photos/aljazeeraenglish/albums/72157626164453131/",
                    "csrf_token": "1234",
                },
            )

    assert resp.status_code == 200
    assert (
        b'value="https://www.flickr.com/photos/aljazeeraenglish/albums/72157626164453131/"'
        in resp.data
    )
