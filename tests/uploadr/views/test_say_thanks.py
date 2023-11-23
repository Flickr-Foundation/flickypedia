from flask.testing import FlaskClient


def test_say_thanks_page(logged_in_client: FlaskClient, queue_dir: None) -> None:
    resp = logged_in_client.get("/say_thanks/7bb77a24-ae46-4196-8269-392cfa9e1df3")

    assert resp.status_code == 200
    assert b"There are two ways to say thanks" in resp.data
