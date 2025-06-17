from flask.testing import FlaskClient


def test_upload_complete(logged_in_client: FlaskClient, queue_dir: None) -> None:
    resp = logged_in_client.get("/upload_complete/7bb77a24-ae46-4196-8269-392cfa9e1df3")

    assert resp.status_code == 200
    assert "Upload complete!" in resp.text


def test_upload_complete_if_upload_filaed(
    logged_in_client: FlaskClient, queue_dir: None
) -> None:
    resp = logged_in_client.get("/upload_complete/a23be662-4f3f-41fa-8f86-ac21ddb50e58")

    assert resp.status_code == 200
    assert "Upload failed!" in resp.text
