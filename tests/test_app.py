from urllib.parse import urlencode

import pytest


def test_homepage(client):
    resp = client.get("/")
    assert b"Welcome to Flickypedia!" in resp.data


@pytest.mark.parametrize("path", ["/logout", "/find_photos", "/prepare_info"])
def test_redirected_to_homepage_for_pages_requiring_login(client, path):
    resp = client.get(path)
    assert resp.status_code == 302

    params = urlencode({"next": path})
    assert resp.headers["location"] == f"/?{params}"
