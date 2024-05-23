import os

from flask.testing import FlaskClient
from flask_login import current_user
import pytest


@pytest.fixture
def oauth_env_vars() -> None:
    os.environ.setdefault("FLICKR_CLIENT_ID", "123")
    os.environ.setdefault("FLICKR_CLIENT_SECRET", "456")


def test_can_get_token_from_flickr(
    oauth_env_vars: None,
    logged_in_client: FlaskClient,
    flickr_oauth_cassette: str,
    user_agent: str,
) -> None:
    """
    This test verifies that our login code works.

    I had to be a bit careful with this, because I had to use our real
    OAuth credentials to set up this test.

    What I did:

    1.  Ran the first half of the test, up to the commented-out ``assert 0``.
        This gave me a real authorization URL I could open in Flickr.

    2.  I clicked that authorization URL, which took me to a localhost:5000/…
        URL.  I pasted that into the callback_resp line, and matched the state
        to the session cookie.

    3.  I ran the entire test, with the ``assert 0`` commented out.  This did
        the token exchange with Flickr.

    4.  I redacted the secrets from the URL and the VCR cassette.

    """
    os.environ.setdefault("FLICKR_CLIENT_ID", "123")
    os.environ.setdefault("FLICKR_CLIENT_SECRET", "456")

    # Check that we aren't currently logged in to Flickr.
    assert current_user.encrypted_flickr_token is None

    # Take the user to the login endpoint.  See where we get redirected.
    authorize_resp = logged_in_client.get(
        "/authorize/flickr?next_url=http://localhost:5000/post_comments"
    )
    location = authorize_resp.headers["location"]

    # Print that URL -- open this in a browser separately, and make note of where
    # I was redirected.
    print(location)
    # assert 0

    # Now pass the redirect URL in here, as if I had been redirected to the
    # test client.
    callback_resp = logged_in_client.get(
        "/callback/flickr?oauth_token=72157720902560356-b280a7d3716a97e2&oauth_verifier=3c934d75060f9aa6"
    )

    assert callback_resp.status_code == 302
    assert callback_resp.headers["location"] == "http://localhost:5000/post_comments"

    # Now check that there's an encrypted Flickr token saved in the database
    assert current_user.encrypted_flickr_token is not None
    assert current_user.flickr_token() == {
        "fullname": "Alex Chan",
        "oauth_token": "ACCESS_TOKEN_0b3",
        "oauth_token_secret": "ACCESS_TOKEN_SECRET_f04",
        "user_nsid": "199246608@N02",
        "username": "cefarrjf87",
    }

    # Now check that if I try to log in a second time, I'm sent directly
    # to my target, not back to Flickr's OAuth.
    second_login_resp = logged_in_client.get(
        "/authorize/flickr?next_url=http://localhost:5000/post_comments"
    )

    assert second_login_resp.status_code == 302
    assert (
        second_login_resp.headers["location"] == "http://localhost:5000/post_comments"
    )
