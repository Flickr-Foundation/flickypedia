import datetime
import json
import os

from authlib.oauth2.rfc6749.wrappers import OAuth2Token
from cryptography.fernet import Fernet
from flask import Flask, session
from flask.testing import FlaskClient
from flask_login import current_user, login_user

from flickypedia.uploadr.auth import (
    load_user,
    user_db,
    WikimediaUserSession,
    SESSION_ENCRYPTION_KEY,
)
from flickypedia.utils import encrypt_string


def store_user(token: OAuth2Token | None = None) -> WikimediaUserSession:
    """
    Create a user and store them in the database.

    This simulates a "real" login and is the preferred way to create
    logged-in users during tests – once you do this, the rest of
    the app code should treat this just like a real user.

    This minimises the need to include this sort of conditional in
    our auth code:

        if app.config["TESTING"]:
            # do thing which bypasses regular auth

    which is nice, because then there's no risk of those lower-security
    branches being inadvertently run in prod code.

    Note: this is a close duplicate of a function with the same name in
    ``utils.py``; having divergent implementations has been easier than
    trying to wrangle sessions correctly across all the uses.

    """
    oauth2_token = token or OAuth2Token(
        {
            "token_type": "Bearer",
            "expires_in": 14400,
            "access_token": "[ACCESS_TOKEN...sqfLY]",
            "refresh_token": "[REFRESH_TOKEN...8f34f]",
            "expires_at": 2299322615,
        }
    )

    key = Fernet.generate_key()

    session[SESSION_ENCRYPTION_KEY] = key

    # (I haven't actually checked this, but I'm pretty sure user IDs
    # in Wikimedia are all positive integers.)
    user = WikimediaUserSession(
        id="-4",
        userid="-4",
        name="FlickypediaTestingUser",
        encrypted_token=encrypt_string(key, plaintext=json.dumps(oauth2_token)),
        first_login=datetime.datetime.now(),
    )
    user_db.session.add(user)
    user_db.session.commit()

    login_user(user)

    return user


class TestOAuth2AuthorizeWikimedia:
    def test_new_user_is_redirected_to_wikimedia(self, app: Flask) -> None:
        app.config["OAUTH_PROVIDERS"]["wikimedia"]["client_id"] = "example1234"

        with app.test_client() as client:
            resp = client.get("/authorize/wikimedia")

        assert resp.status_code == 302
        assert resp.headers["location"].startswith(
            "https://meta.wikimedia.org/w/rest.php/oauth2/authorize?response_type=code&client_id=example1234&state="
        )

    def test_logged_in_user_is_redirected_to_get_photos(
        self, logged_in_client: FlaskClient
    ) -> None:
        resp = logged_in_client.get("/authorize/wikimedia")

        # If you're already logged in, you should be redirected
        assert resp.status_code == 302
        assert resp.headers["location"] == "/get_photos"


class TestLogOut:
    def test_logging_out_redirects_to_homepage(
        self, logged_in_client: FlaskClient
    ) -> None:
        logout_resp = logged_in_client.get("/logout")

        # After you're logged out, you should be redirected to the homepage
        assert logout_resp.status_code == 302
        assert logout_resp.headers["location"] == "/"

        # After you've logged out, trying to re-authorize with Wikimedia
        # should send you off to their auth screen rather than straight
        # back into Flickypedia.
        auth_resp = logged_in_client.get("/authorize/wikimedia")
        assert auth_resp.headers["location"].startswith("https://meta.wikimedia.org/")

    def test_logging_out_removes_current_user(
        self, logged_in_client: FlaskClient
    ) -> None:
        assert not current_user.is_anonymous

        logged_in_client.get("/logout")

        assert current_user.is_anonymous

    def test_logging_out_removes_user_from_user_db(
        self, logged_in_client: FlaskClient
    ) -> None:
        assert len(user_db.session.query(WikimediaUserSession).all()) == 1

        logged_in_client.get("/logout")

        assert len(user_db.session.query(WikimediaUserSession).all()) == 0

    def test_logging_out_removes_encryption_key_from_session(
        self, logged_in_client: FlaskClient
    ) -> None:
        session[SESSION_ENCRYPTION_KEY] = "<sekrit key>"

        logged_in_client.get("/logout")

        assert SESSION_ENCRYPTION_KEY not in session


class TestOAuth2CallbackWikimedia:
    def test_already_logged_in_bypasses_flow(
        self, logged_in_client: FlaskClient
    ) -> None:
        resp = logged_in_client.get("/callback/wikimedia")

        # If you're already logged in, you don't need to come through
        # this flow.
        assert resp.status_code == 302
        assert resp.headers["location"] == "/get_photos"

    def test_missing_state_is_error(self, client: FlaskClient) -> None:
        resp = client.get("/callback/wikimedia?code=12345")

        assert resp.status_code == 401

    def test_missing_code_is_error(
        self, client: FlaskClient, vcr_cassette: str
    ) -> None:
        with client.session_transaction() as session:
            session["oauth_authorize_state"] = "1234"

        resp = client.get("/callback/wikimedia?state=XYZ")

        assert resp.status_code == 401

    def test_mismatched_code_is_error(
        self, client: FlaskClient, vcr_cassette: str
    ) -> None:
        with client.session_transaction() as session:
            session["oauth_authorize_state"] = "1234"

        resp = client.get("/callback/wikimedia?code=ABC&state=XYZ")

        assert resp.status_code == 401

    def test_bad_token_from_wikimedia_is_error(
        self, app: Flask, vcr_cassette: str
    ) -> None:
        app.config["OAUTH_PROVIDERS"]["wikimedia"].update(
            {
                "client_id": "client1234",
                "client_secret": "client1234",
            }
        )

        with app.test_client() as client:
            resp = client.get("/callback/wikimedia?code=123")

        assert resp.status_code == 401


class TestOAuth2AuthorizeFlickr:
    def test_missing_next_url_is_error(self, logged_in_client: FlaskClient) -> None:
        resp = logged_in_client.get("/authorize/flickr")

        assert resp.status_code == 400


class TestOAuth2CallbackFlickr:
    def test_missing_request_token_in_session_is_error(
        self, logged_in_client: FlaskClient
    ) -> None:
        resp = logged_in_client.get("/callback/flickr?oauth_token=123")

        assert resp.status_code == 400


def test_token_is_saved_to_database_when_refreshed(
    app: Flask, client: FlaskClient, vcr_cassette: str
) -> None:
    """
    Periodically, we call the ``ensure_active_token()`` to make sure
    we still have a valid token for use with the Wikimedia API.

    This test checks that this method will update the token if necessary.

    Note: as with some other tests that involve credentials, I initially
    ran this with my real credentials, then I went back and redacted the
    VCR cassette for safety.
    """
    with app.test_request_context():
        try:  # pragma: no cover
            token = json.loads(os.environ["WIKIMEDIA_ACCESS_TOKEN"])
        except KeyError:  # pragma: no cover
            token = {
                "token_type": "Bearer",
                "expires_in": 14400,
                "access_token": "[ACCESS_TOKEN...sqfLY]",
                "refresh_token": "[REFRESH_TOKEN...8f34f]",
                "expires_at": 1699322615,
            }

        # Modify the 'expires_at' time, so it's actually 1 second ago -- as far
        # as authlib is concerned, this token is now invalid.
        token["expires_at"] = int(datetime.datetime.now().timestamp() - 1)

        # Now save a user with this token to the database.
        user = store_user(token=token)

        # Check that if we retrieve the token, it's the one that was stored.
        assert user.token() == token

        # Now call the ensure_active_token() token method.  This should force
        # a token refresh.
        user.ensure_active_token()

        # Check that the user's token no longer matches the one we saved earlier.
        assert user.token() != token
        assert user.token()["expires_at"] > datetime.datetime.now().timestamp()  # type: ignore

        refreshed_token = user.token()

        # Now call ensure_active_token() a second time, and check that we don't
        # get a refresh, because we already have an up-to-date token.
        user.ensure_active_token()
        assert user.token() == refreshed_token


class TestLoadUser:
    def test_no_matching_id_is_no_user(self, app: Flask) -> None:
        app.config["TESTING"] = False

        with app.test_request_context():
            assert load_user(userid="-1") is None

    def test_user_with_inactive_token_is_no_user(
        self, app: Flask, client: FlaskClient, vcr_cassette: str
    ) -> None:
        app.config["TESTING"] = False

        token = OAuth2Token(
            {
                "token_type": "Bearer",
                "expires_in": 14400,
                "access_token": "[ACCESS_TOKEN...sqfLY]",
                "refresh_token": "[REFRESH_TOKEN...8f34f]",
                "expires_at": -1,
            }
        )

        with app.test_request_context():
            user = store_user(token=token)

            assert load_user(userid=user.id) is None

    def test_returns_user_with_active_token(self, app: Flask) -> None:
        app.config["TESTING"] = False

        token = OAuth2Token(
            {
                "token_type": "Bearer",
                "expires_in": 14400,
                "access_token": "[ACCESS_TOKEN...sqfLY]",
                "refresh_token": "[REFRESH_TOKEN...8f34f]",
                "expires_at": datetime.datetime.now().timestamp() + 3600,
            }
        )

        with app.test_request_context():
            user = store_user(token)

            assert load_user(userid=user.id) == user
