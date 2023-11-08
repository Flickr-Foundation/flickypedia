"""
Everything related to user authentication.

In particular, this file should contain all the code related to users
authenticating with the Wikimedia and Flickr APIs.  The goal is to keep
this all in one place so it can be considered and reviewed as a single
unit -- this is the most sensitive code in the app.

== Design notes ==

We use Wikimedia's OAuth 2.0 user credentials flow.

When we want to authenticate a user with Wikimedia, we send them to
a URL on meta.wikimedia.org where they log in and approve our app.
They then get redirected back to Flickypedia with an authorization code,
which we can exchange for an access/refresh token.  We can then use the
access token to authenticate requests with the Wikimedia API on behalf
of the logged-in user.

This leaves us with a design question: where do we store the access tokens?

Quoting some advice from Auth0:

    If your app needs to call APIs on behalf of the user, access tokens
    and (optionally) refresh tokens are needed. These can be stored
    server-side or in a session cookie.

In Flickypedia, we store the tokens server-side.

Because these tokens can be used to perform actions on behalf of a user
in the Wikimedia universe, we need to keep them secure.  When we get
an access token for a session, we create a unique encryption key using
the ``cryptography`` library, and we use this to encrypt the tokens.

*   The encryption key is stored in the user's client-side session
*   The encrypted tokens are stored in our server-side database

This means that somebody who gets access to the server-side database
can't just read out all the user tokens, and somebody who gets access
to the user's browser can't just retrieve their token.

== External interface ==

Flask passes around state in global variables (``request``, ``session``,
etc.) and Flask-Login follows this pattern with ``current_user``.

Whenever code outside this file needs to get an authenticated resource,
it should be accessing it via ``current_user``.

== Useful background reading ==

*   Wikimedia OAuth 2.0 user authentication flow
    https://api.wikimedia.org/wiki/Authentication

*   Miguel Grinberg's "OAuth Authentication with Flask in 2023"
    https://blog.miguelgrinberg.com/post/oauth-authentication-with-flask-in-2023

*   Miguel Grinberg's "How Secure Is The Flask User Session?" (not very!)
    https://blog.miguelgrinberg.com/post/how-secure-is-the-flask-user-session

*   Auth0's "Token Storage" docs
    https://auth0.com/docs/secure/security-guidance/data-security/token-storage

*   OAuth 2 Session in the authlib docs:
    https://docs.authlib.org/en/latest/client/oauth2.html

"""

import json
from typing import Optional
import uuid

from authlib.integrations.httpx_client.oauth2_client import OAuth2Client
from authlib.oauth2.rfc6749.wrappers import OAuth2Token
from cryptography.fernet import Fernet
from flask import abort, current_app, flash, redirect, request, session, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_sqlalchemy import SQLAlchemy
import httpx

from flickypedia.apis.wikimedia import WikimediaApi
from flickypedia.utils import decrypt_string, encrypt_string
from flickypedia.views._types import ViewResponse


user_db = SQLAlchemy()

login = LoginManager()
login.login_view = "homepage"


# This is the name of the encryption key which is stored in the user session.
SESSION_ENCRYPTION_KEY = "oauth_key_wikimedia"


class WikimediaUserSession(UserMixin, user_db.Model):  # type: ignore
    """
    Represents a single session for a logged-in Wikimedia user.
    This model is written to a SQLite database that lives on the server,
    so it shouldn't contain any secret information in plaintext.
    """

    __tablename__ = "wikimedia_user_sessions"
    id = user_db.Column(user_db.String(64), primary_key=True)
    userid = user_db.Column(user_db.Integer, nullable=False)
    name = user_db.Column(user_db.String(64), nullable=False)
    encrypted_token = user_db.Column(user_db.LargeBinary, nullable=False)

    def get_id(self) -> str:
        """
        This method is used by Flask-Login to identify the user's session.

        See https://flask-login.readthedocs.io/en/latest/#your-user-class
        """
        return self.id  # type: ignore

    @property
    def profile_url(self) -> str:
        """
        Returns a link to the user's profile on Wikimedia Commons.
        """
        return f"https://commons.wikimedia.org/wiki/User:{self.name}"

    @property
    def uploads_url(self) -> str:
        """
        Returns a link to the user's uploads on Wikimedia Commons.
        """
        return f"https://commons.wikimedia.org/w/index.php?title=Special:ListFiles/{self.name}&ilshowall=1"

    def token(self) -> OAuth2Token:
        """
        Retrieve the unencrypted value of the user's token.

        This can only be called in the context of a logged-in Flask session,
        where we have access to the per-session encryption key.
        """
        decrypted_token = decrypt_string(
            key=session[SESSION_ENCRYPTION_KEY], ciphertext=self.encrypted_token
        )

        params = json.loads(decrypted_token)

        return OAuth2Token(params)

    def _oauth2_client(self) -> OAuth2Client:
        """
        Returns a configured OAuth2 client.
        """
        headers = {"User-Agent": current_app.config["USER_AGENT"]}

        def update_token(token: OAuth2Token, refresh_token: str) -> None:
            self.encrypted_token = encrypt_string(
                key=session[SESSION_ENCRYPTION_KEY], plaintext=json.dumps(token)
            )
            user_db.session.commit()

        config = current_app.config["OAUTH2_PROVIDERS"]["wikimedia"]

        return OAuth2Client(
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            authorization_endpoint=config["authorize_url"],
            token_endpoint=config["token_url"],
            token=self.token(),
            # If/when the token is updated (using a refresh token), ensure
            # we update the value in the database.
            update_token=update_token,
            headers=headers,
        )

    def ensure_active_token(self) -> None:
        """
        Check that the user's token is active, and if not, use the refresh token
        to update it.
        """
        client = self._oauth2_client()
        client.ensure_active_token(token=self.token())

    def refresh_token(self) -> None:
        """
        Regardless of the current state of the user's session, get
        a new token -- this will ensure the current access token is valid
        for another four hours.
        """
        config = current_app.config["OAUTH2_PROVIDERS"]["wikimedia"]

        client = self._oauth2_client()
        client.refresh_token(url=config["token_url"])

    def wikimedia_api(self) -> WikimediaApi:
        """
        Returns a Wikimedia API client which is authenticated for this user.
        """
        client: httpx.Client

        try:
            client = self._oauth2_client()
        except KeyError:
            # During tests, it's okay to use an unauthenticated client, because
            # we aren't dealing with real sessions or real credentials --
            # we're just replaying API interactions from the VCR cassettes.
            assert current_app.config["TESTING"]
            client = httpx.Client()

        return WikimediaApi(client=client)

    def delete(self) -> None:
        """
        Remove the user from the database.  This will effectively end
        their login session, as we no longer have any OAuth credentials
        for them.
        """
        # Delete both parts of the user's session: the encrypted copy of
        # their OAuth tokens in the server-side database, and the encryption
        # key in their session cookie.
        user_db.session.query(WikimediaUserSession).filter(
            WikimediaUserSession.id == current_user.id
        ).delete()
        user_db.session.commit()

        # Admittedly it would be unusual if the user didn't have an
        # encryption key in their session cookie, but if they don't, it
        # shouldn't stop the logout process.
        try:
            del session[SESSION_ENCRYPTION_KEY]
        except KeyError:
            pass


@login.user_loader
def load_user(userid: str) -> Optional[WikimediaUserSession]:
    """
    Load a user.  This includes checking that we still have valid
    Wikimedia credentials for them.

    This is a method required by Flask-Login.

    See https://flask-login.readthedocs.io/en/latest/#flask_login.LoginManager.user_loader
    """
    if current_app.config.get("TESTING"):
        return WikimediaUserSession(id=-1, userid=-1, name="example")
    else:
        user = user_db.session.get(WikimediaUserSession, userid)

        if user is None:
            return None

        # Ensure the user has a OAuth token which is still active -- either
        # created recently enough that it's still valid, or we have a valid
        # refresh token we can use to get a new token.
        #
        # If this fails for some reason, we should log the user out.
        try:
            user.ensure_active_token()
        except Exception as exc:
            print(f"Unable to ensure active token for {user}: {exc}")
            user.delete()
            return None
        else:
            return user


@login_required
def logout() -> ViewResponse:
    """
    A route to log out the user.
    """
    current_user.delete()

    logout_user()

    return redirect(url_for("homepage"))


def oauth2_authorize_wikimedia() -> ViewResponse:
    """
    Authorize the user with the Wikimedia APIs.

    This is a named route which redirects so we can access it
    with ``url_for()`` in templates.
    """
    # If you're already logged in, you don't need to come through
    # this flow.
    if not current_user.is_anonymous:
        return redirect(url_for("get_photos"))

    # Create a URL that takes the user to a page on meta.wikimedia.org
    # where they can log in with their Wikimedia account and approve
    # an authorization request.
    #
    # This is the URL described in step 2 of
    # https://api.wikimedia.org/wiki/Authentication#2._Request_authorization
    config = current_app.config["OAUTH2_PROVIDERS"]["wikimedia"]

    client = OAuth2Client(client_id=config["client_id"])

    uri, state = client.create_authorization_url(url=config["authorize_url"])

    session["oauth_authorize_state"] = state

    return redirect(uri)


def oauth2_callback_wikimedia() -> ViewResponse:
    """
    Handle an authorization callback from Wikimedia.
    """
    # If you're already logged in, you don't need to come through
    # this flow.
    if not current_user.is_anonymous:
        return redirect(url_for("get_photos"))

    # Exchange the authorization response for an access token
    try:
        state = session.pop("oauth_authorize_state")
    except KeyError:
        print("Unable to retrieve oauth_authorize_state from user's session")
        abort(401)

    config = current_app.config["OAUTH2_PROVIDERS"]["wikimedia"]
    token_client = OAuth2Client(
        client_id=config["client_id"],
        client_secret=config["client_secret"],
        token_endpoint=config["token_url"],
    )

    try:
        token = token_client.fetch_token(
            token_endpoint=config["token_url"],
            authorization_response=request.url,
            state=state,
        )
    except Exception as exc:
        print(f"Error exchanging authorization code for token: {exc}")
        abort(401)

    # Get info about the logged in user
    wiki_client = httpx.Client(
        headers={
            "Authorization": f"Bearer {token['access_token']}",
            "User-Agent": current_app.config["USER_AGENT"],
        }
    )
    api = WikimediaApi(client=wiki_client)
    userinfo = api.get_userinfo()

    # Now create a user and store it in the database.
    #
    # In Miguel Grinberg's code, he looks for an existing user.  We don't
    # have to do that here, because we're creating per-session database
    # entries.  We know there isn't an existing user.
    key = Fernet.generate_key()

    session[SESSION_ENCRYPTION_KEY] = key

    user = WikimediaUserSession(
        id=str(uuid.uuid4()),
        userid=userinfo["id"],
        name=userinfo["name"],
        encrypted_token=encrypt_string(key, plaintext=json.dumps(token)),
    )
    user_db.session.add(user)
    user_db.session.commit()

    # Log the user in
    login_user(user)

    flash("You’re logged in.", category="login_header")

    return redirect(url_for("get_photos"))
