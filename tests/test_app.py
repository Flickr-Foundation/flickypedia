from urllib.parse import urlencode

from flask import FlaskClient
import pytest


def test_homepage(client: FlaskClient) -> None:
    resp = client.get("/")
    assert b"Flickypedia helps you put Flickr photos in Wikimedia Commons" in resp.data

    assert b"Log in" in resp.data
    assert b"to Wikimedia Commons" in resp.data


def test_homepage_shows_user_info_if_logged_in(logged_in_client: FlaskClient) -> None:
    resp = logged_in_client.get("/")
    assert "you’re logged in as" in resp.data.decode("utf8")


@pytest.mark.parametrize(
    "path",
    [
        "/logout",
        "/get_photos",
        "/select_photos",
    ],
)
def test_redirected_to_homepage_for_pages_requiring_login(
    client: FlaskClient, path: str
) -> None:
    resp = client.get(path)
    assert resp.status_code == 302

    params = urlencode({"next": path})
    assert resp.headers["location"] == f"/?{params}"
