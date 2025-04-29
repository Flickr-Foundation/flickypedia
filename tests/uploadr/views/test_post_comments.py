from flask.testing import FlaskClient
from flickr_api import FlickrApi


def test_post_comments_page(
    logged_in_client: FlaskClient, flickr_api: FlickrApi, queue_dir: None
) -> None:
    resp = logged_in_client.get(
        "/post_comments/7bb77a24-ae46-4196-8269-392cfa9e1df3?user=bot"
    )

    assert resp.status_code == 200
    assert "We’ll post on your behalf as Flickypedia Bot" in resp.data.decode("utf8")


def test_no_user_arg_is_error(logged_in_client: FlaskClient) -> None:
    resp = logged_in_client.get("/post_comments/7bb77a24-ae46-4196-8269-392cfa9e1df3")

    assert resp.status_code == 400


def test_unrecognised_user_arg_is_error(logged_in_client: FlaskClient) -> None:
    resp = logged_in_client.get(
        "/post_comments/7bb77a24-ae46-4196-8269-392cfa9e1df3?user=alex"
    )

    assert resp.status_code == 400
