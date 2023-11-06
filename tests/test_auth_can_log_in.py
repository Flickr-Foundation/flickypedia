from flask_login import current_user


def test_can_get_token_from_wikimedia(client, vcr_cassette):
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
    assert current_user == None

    authorize_resp = client.get("/authorize/wikimedia")

    location = authorize_resp.headers['location']

    print(location)
    # assert 0

    with client.session_transaction() as session:
        session['oauth_authorize_state'] = 'XertqAsuJqXjgns0v9fHXUKeK3gwcf'

    callback_resp = client.get(
        '/callback/wikimedia?code=[CODE]&state=XertqAsuJqXjgns0v9fHXUKeK3gwcf'
    )

    assert callback_resp.headers['location'] == '/get_photos'

    token = current_user.token()
    del token['expires_at']
    assert token == {
        'token_type': 'Bearer',
        'expires_in': 14400,
        'access_token': 'ACCESS_TOKEN',
        'refresh_token': 'REFRESH_TOKEN',
    }
