from flask.testing import FlaskClient


def test_keep_going(logged_in_client: FlaskClient) -> None:
    resp = logged_in_client.get("/keep_going")

    assert b"<h2>Would you like to keep going?</h2>" in resp.data
