import json

from flask.testing import FlaskClient


def test_wait_for_upload_redirects_if_complete(
    logged_in_client: FlaskClient, celery_dir: None
) -> None:
    resp = logged_in_client.get("/wait_for_upload/7bb77a24-ae46-4196-8269-392cfa9e1df3")

    assert resp.status_code == 302
    assert (
        resp.headers["location"]
        == "/upload_complete/7bb77a24-ae46-4196-8269-392cfa9e1df3"
    )


def test_wait_for_upload_waits_if_in_progress(
    logged_in_client: FlaskClient, celery_dir: None
) -> None:
    resp = logged_in_client.get("/wait_for_upload/e358876e-f3d6-439b-85fa-1ed1e46338ec")

    assert resp.status_code == 200
    assert b"1 of 1" in resp.data


def test_wait_for_upload_api(logged_in_client: FlaskClient, celery_dir: None) -> None:
    resp = logged_in_client.get(
        "/wait_for_upload/e358876e-f3d6-439b-85fa-1ed1e46338ec/status"
    )

    data = json.loads(resp.data)

    assert not data["ready"]
    assert len(data["progress"]) == 1
