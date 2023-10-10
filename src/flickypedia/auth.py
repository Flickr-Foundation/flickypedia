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

"""

import datetime
from urllib.parse import urlencode
import uuid

from cryptography.fernet import Fernet
from flask import abort, flash, redirect, request, session, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
import httpx

from flickypedia import app, db
from flickypedia.apis.wikimedia import get_userinfo
from flickypedia.utils import decrypt_string, encrypt_string


login = LoginManager(app)
login.login_view = "index"


# Every user gets a session ID which matches their entry in the database
# of access tokens.  This ID is an opaque identifier that avoids us
# having to deal with e.g. the same user logged in on two computers.
#
# This is the name of the key that ID is stored under in their session.
SESSION_ID_KEY = "oauth_userid_wikimedia"

# This is the name of the encryption key which is stored in the user session.
SESSION_ENCRYPTION_KEY = "oauth_key_wikimedia"


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
    encrypted_access_token = db.Column(db.LargeBinary, nullable=False)
    access_token_expires = db.Column(db.DateTime, nullable=False)
    encrypted_refresh_token = db.Column(db.LargeBinary, nullable=False)

    def access_token(self, key):
        return decrypt_string(key, ciphertext=self.encrypted_access_token)

    def refresh_token(self, key):
        return decrypt_string(key, ciphertext=self.encrypted_refresh_token)


@login.user_loader
def load_user(session_id: str):
    return db.session.get(WikimediaUserSession, session[SESSION_ID_KEY])


@app.route("/logout")
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

    flash("You have been logged out.")
    return redirect(url_for("index"))


@app.route("/authorize/wikimedia")
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
        return redirect(url_for("index"))

    provider_data = app.config["OAUTH2_PROVIDERS"]["wikimedia"]

    # Create a URL that takes the user to a page on meta.wikimedia.org
    # where they can log in with their Wikimedia account and approve
    # an authorization request.
    #
    # This is the URL described in step 2 of
    # https://api.wikimedia.org/wiki/Authentication#2._Request_authorization
    qs = urlencode(
        {
            "client_id": provider_data["client_id"],
            "response_type": "code",
        }
    )

    return redirect(provider_data["authorize_url"] + "?" + qs)


@app.route("/callback/wikimedia")
def oauth2_callback_wikimedia():
    """
    Handle an authorization callback from Wikimedia.
    """
    # If you're already logged in, you don't need to come through
    # this flow.
    if not current_user.is_anonymous:
        return redirect(url_for("index"))

    # TODO: This is copied out of Miguel Grinberg's Flask tutorial.
    #
    # It seems benign enough, but does the Wikimedia redirect ever
    # actually include this parameter?
    if "error" in request.args:
        for k, v in request.args.items():
            flash(f"{k}: {v}")
        return redirect(url_for("index"))

    # Make sure the authorization code is present
    try:
        authorization_code = request.args["code"]
    except KeyError:
        flash("No authorization code in callback")
        abort(401)

    # Exchange the authorization code for an access token
    provider_data = app.config["OAUTH2_PROVIDERS"]["wikimedia"]

    resp = httpx.post(
        provider_data["token_url"],
        data={
            "grant_type": "authorization_code",
            "code": authorization_code,
            "client_id": provider_data["client_id"],
            "client_secret": provider_data["client_secret"],
        },
    )

    if resp.status_code != 200:
        flash("Error while getting access token from Wikimedia")
        abort(401)

    # Extract the key values from the token response.
    #
    # As well as the ``access_token`` and ``refresh_token`` fields
    # described in their docs, Wikimedia also returns an ``expires``
    # field which tells us how long the access token will last.
    try:
        access_token = resp.json()["access_token"]
        refresh_token = resp.json()["refresh_token"]
        expires_in = resp.json()["expires_in"]
    except KeyError:
        flash("Malformed access token response from Wikimedia")
        abort(401)

    # Get info about the logged in user
    userinfo = get_userinfo(access_token=access_token)

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
        encrypted_access_token=encrypt_string(key, plaintext=access_token),
        access_token_expires=datetime.datetime.now()
        + datetime.timedelta(seconds=expires_in),
        encrypted_refresh_token=encrypt_string(key, plaintext=refresh_token),
    )
    db.session.add(user)
    db.session.commit()

    # Log the user in
    login_user(user)

    return redirect(url_for("index"))
