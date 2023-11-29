from flask.testing import FlaskClient


def test_can_load_about_page(client: FlaskClient) -> None:
    resp = client.get("/about/")

    assert b"<h2>About Flickypedia</h2>" in resp.data


def test_privacy_policy_links_to_logged_in_users_uploads(
    logged_in_client: FlaskClient,
) -> None:
    resp = logged_in_client.get("/about/")

    assert (
        b'<a href="https://commons.wikimedia.org/w/index.php?title=Special:ListFiles/FlickypediaTestingUser&ilshowall=1">your public upload history</a>'
        in resp.data
    )


def test_can_load_bookmarklet(client: FlaskClient) -> None:
    resp = client.get("/bookmarklet/")

    assert b"<h2>Flickypedia bookmarklet</h2>" in resp.data
