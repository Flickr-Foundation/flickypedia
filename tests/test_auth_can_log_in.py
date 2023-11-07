import datetime

from flask import FlaskClient
from flask_login import current_user


def test_can_get_token_from_wikimedia(
    client: FlaskClient, vcr_cassette: str, user_agent: str
) -> None:
    """
    This test verifies that our login code works.

    I had to be a bit careful with this, because I had to use our real
    OAuth credentials to set up this test.

    What I did:

    1.  Ran the first half of the test, up to the commented-out ``assert 0``.
        This gave me a real authorization URL I could open in Wikimedia.

    2.  I clicked that authorization URL, which took me to a localhost:5000/…
        URL.  I pasted that into the callback_resp line, and matched the state
        to the session cookie.

    3.  I ran the entire test, with the ``assert 0`` commented out.  This did
        the token exchange with Wikimedia.

    4.  I redacted the secrets from the URL and the VCR cassette.

    """
    # Check we aren't currently logged in.  Normally this would be an anonymous
    # user, but I haven't got that working with Flask-Login and tests.
    assert current_user == None  # noqa: E711

    # Take the user to the loign endpoint.  See where we get redirected.
    authorize_resp = client.get("/authorize/wikimedia")
    location = authorize_resp.headers["location"]

    # Print that URL -- open this in a browser separately, and make note of where
    # I was redirected.
    print(location)
    # assert 0

    # Now pass the redirect URL in here, as if I had been redirected to the
    # test client.
    with client.session_transaction() as session:
        session["oauth_authorize_state"] = "7E7Nw3ZzjpVkOnPcQHxEm4LeIih1CU"

    callback_resp = client.get(
        "/callback/wikimedia?code=[CODE]&state=7E7Nw3ZzjpVkOnPcQHxEm4LeIih1CU"
    )

    # Check I've been logged in and redirected to the "get photos" page
    assert callback_resp.headers["location"] == "/get_photos"
    assert not current_user.is_anonymous

    # Now check the value of the current user's token.
    #
    # The 'expires_at' will vary based on when the token was retrieved, so
    # ignore it.
    token = current_user.token()

    expected_token = {
        "token_type": "Bearer",
        "expires_in": 14400,
        "access_token": "[ACCESS_TOKEN...sqfLY]",
        "refresh_token": "[REFRESH_TOKEN...8f34f]",
    }

    assert all(token[k] == expected_token[k] for k in expected_token)

    # Now futz with the token -- set it to have just expired.  This should
    # force the OAuth client to refresh the token on the next request.
    token["expires_at"] = int(datetime.datetime.now().timestamp()) - 1

    # Construct an instance of the Wikimedia OAuth API, and check the token
    # is refreshed.  Check also that it's been stored.
    api = current_user.wikimedia_api()
    api.get_userinfo()

    assert api.client.token != token  # type: ignore
    assert api.client.token == current_user.token()  # type: ignore
