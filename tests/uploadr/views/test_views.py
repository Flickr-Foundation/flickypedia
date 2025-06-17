from flask.testing import FlaskClient


def test_can_load_about_page(client: FlaskClient) -> None:
    resp = client.get("/about/")

    assert "<h1>About Flickypedia</h1>" in resp.text


def test_privacy_policy_links_to_logged_in_users_uploads(
    logged_in_client: FlaskClient,
) -> None:
    resp = logged_in_client.get("/about/")

    assert (
        '<a href="https://commons.wikimedia.org/w/index.php?title=Special:ListFiles/FlickypediaTestingUser&ilshowall=1">your public upload history</a>'
        in resp.text
    )


def test_can_load_bookmarklet(client: FlaskClient) -> None:
    resp = client.get("/bookmarklet/")

    assert "<h1>Flickypedia bookmarklet</h1>" in resp.text


def test_can_load_faqs(client: FlaskClient) -> None:
    resp = client.get("/faqs/")

    assert "<h1>Frequently Asked Questions</h1>" in resp.text
