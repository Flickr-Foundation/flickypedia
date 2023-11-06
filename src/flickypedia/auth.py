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
import uuid

from authlib.integrations.httpx_client.oauth2_client import OAuth2Client
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

from flickypedia.apis.wikimedia import WikimediaOAuthApi
from flickypedia.utils import decrypt_string, encrypt_string


db = SQLAlchemy()

login = LoginManager()
login.login_view = "homepage"


# Every user gets a session ID which matches their entry in the database
# of access tokens.  This ID is an opaque identifier that avoids us
# having to deal with e.g. the same user logged in on two computers.
#
# This is the name of the key that ID is stored under in their session.
SESSION_ID_KEY = "oauth_userid_wikimedia"

# This is the name of the encryption key which is stored in the user session.
SESSION_ENCRYPTION_KEY = "oauth_key_wikimedia"


def get_oauth_client() -> OAuth2Client:
    """
    Creates an OAuth2 client which uses our app credentials to connect to Wikimedia.
    """
    config = current_app.config["OAUTH2_PROVIDERS"]["wikimedia"]

    return OAuth2Client(
        client_id=config["client_id"],
        client_secret=config["client_secret"],
        authorization_endpoint=config["authorize_url"],
        token_endpoint=config["token_url"],
    )


def get_wikimedia_api() -> WikimediaOAuthApi:
    """
    Returns an instance of the Wikimedia OAuth API which is connected for the
    current user.
    """
    client = get_oauth_client()
    token = current_user.token()

    return WikimediaOAuthApi(
        client=client, token=token, user_agent=current_app.config["USER_AGENT"]
    )


class WikimediaUserSession(UserMixin, db.Model):
    """
    Represents a single session for a logged-in Wikimedia user.
    This model is written to a SQLite database that lives on the server,
    so it shouldn't contain any secret information in plaintext.
    """

    __tablename__ = "wikimedia_user_sessions"
    id = db.Column(db.String(64), primary_key=True)
    userid = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(64), nullable=False)
    encrypted_token = db.Column(db.LargeBinary, nullable=False)

    def token(self):
        """
        Retrieve the unencrypted value of the user's token.

        This can only be called in the context of a logged-in Flask session,
        where we have access to the per-session encryption key.
        """
        return json.loads(
            decrypt_string(
                key=session[SESSION_ENCRYPTION_KEY], ciphertext=self.encrypted_token
            )
        )

    def store_new_token(self, new_token):
        """
        Store a new OAuth token in the database.

        This method should only be called when the token has changed.

        This can only be called in the context of a logged-in Flask session,
        where we have access to the per-session encryption key.
        """
        assert dict(new_token) != self.token()

        self.encrypted_token = encrypt_string(
            key=session[SESSION_ENCRYPTION_KEY], plaintext=json.dumps(new_token)
        )
        db.session.commit()

    @property
    def profile_url(self):
        return f"https://commons.wikimedia.org/wiki/User:{self.name}"


@login.user_loader
def load_user(session_id: str):
    if current_app.config.get("TESTING"):
        return WikimediaUserSession(id=-1, userid=-1, name="example")
    else:  # pragma: no cover
        return db.session.get(WikimediaUserSession, session[SESSION_ID_KEY])


@login_required
def logout():
    """
    A route to log out the user.
    """
    # Delete both parts of the user's session: the encrypted copy of
    # their OAuth tokens in the server-side database, and the encryption
    # key in their session cookie.
    db.session.query(WikimediaUserSession).filter(
        id == session["oauth_userid_wikimedia"]
    ).delete()
    db.session.commit()
    del session[SESSION_ID_KEY]

    logout_user()

    return redirect(url_for("homepage"))


def oauth2_authorize_wikimedia():
    """
    Authorize the user with the Wikimedia APIs.

    This is a named route which redirects so we can access it
    with ``url_for()`` in templates.
    """
    # If you're already logged in, you don't need to come through
    # this flow.
    #
    # TODO: What if somebody is logged in but we've lost their OAuth tokens
    # for some reason?  Then they'd need to log out and log back in again.
    if not current_user.is_anonymous:
        return redirect(url_for("get_photos"))

    # Create a URL that takes the user to a page on meta.wikimedia.org
    # where they can log in with their Wikimedia account and approve
    # an authorization request.
    #
    # This is the URL described in step 2 of
    # https://api.wikimedia.org/wiki/Authentication#2._Request_authorization
    client = get_oauth_client()
    uri, state = client.create_authorization_url(
        url=client.metadata["authorization_endpoint"]
    )

    session["oauth_authorize_state"] = state

    return redirect(uri)


def oauth2_callback_wikimedia():
    """
    Handle an authorization callback from Wikimedia.
    """
    # If you're already logged in, you don't need to come through
    # this flow.
    if not current_user.is_anonymous:
        return redirect(url_for("get_photos"))

    # Exchange the authorization response for an access token
    client = get_oauth_client()

    try:
        state = session.pop("oauth_authorize_state")
    except KeyError:
        abort(401)

    try:
        token = client.fetch_token(
            token_endpoint=client.metadata["token_endpoint"],
            authorization_response=request.url,
            state=state,
        )
    except Exception as exc:
        print(f"Error exchanging authorization code for token: {exc}")
        abort(401)

    # Get info about the logged in user
    api = WikimediaOAuthApi(
        client=client, token=token, user_agent=current_app.config["USER_AGENT"]
    )
    userinfo = api.get_userinfo()

    # Add our persistent ID to the session object.
    session[SESSION_ID_KEY] = str(uuid.uuid4())

    # Now create a user and store it in the database.
    #
    # In Miguel Grinberg's code, he looks for an existing user.  We don't
    # have to do that here, because we're creating per-session database
    # entries.  We know there isn't an existing user.
    key = Fernet.generate_key()

    session[SESSION_ENCRYPTION_KEY] = key

    user = WikimediaUserSession(
        id=session[SESSION_ID_KEY],
        userid=userinfo["id"],
        name=userinfo["name"],
        encrypted_token=encrypt_string(key, plaintext=json.dumps(token)),
    )
    db.session.add(user)
    db.session.commit()

    # Log the user in
    login_user(user)

    flash("You’re logged in.", category="login_header")

    return redirect(url_for("get_photos"))
