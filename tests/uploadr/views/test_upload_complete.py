from flask.testing import FlaskClient


def test_upload_complete(logged_in_client: FlaskClient, queue_dir: None) -> None:
    resp = logged_in_client.get("/upload_complete/7bb77a24-ae46-4196-8269-392cfa9e1df3")

    assert resp.status_code == 200
    assert b"Upload complete!" in resp.data
