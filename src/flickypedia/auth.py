"""
Contains all code related to user authentication.

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

> If your app needs to call APIs on behalf of the user, access tokens
> and (optionally) refresh tokens are needed. These can be stored
> server-side or in a session cookie.

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
import os
from urllib.parse import urlencode
import uuid

from cryptography.fernet import Fernet
from flask import abort, flash, redirect, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
import httpx

from flickypedia.app import app
from flickypedia.apis.wikimedia import get_userinfo
from flickypedia.utils import decrypt_string, encrypt_string

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["OAUTH2_PROVIDERS"] = {
    # Implementation note: although these URLs are currently hard-coded,
    # there is a beta cluster we might use in the future.  It's currently
    # broken, so we're not adding support for it yet, but we could if
    # it ever gets fixed.
    #
    # See https://github.com/Flickr-Foundation/flickypedia/issues/4
    "wikimedia": {
        "client_id": os.environ.get("WIKIMEDIA_CLIENT_ID"),
        "client_secret": os.environ.get("WIKIMEDIA_CLIENT_SECRET"),
        "authorize_url": "https://meta.wikimedia.org/w/rest.php/oauth2/authorize",
        "token_url": "https://meta.wikimedia.org/w/rest.php/oauth2/access_token",
    }
}


db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = "index"


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
def load_user(id):
    return db.session.get(WikimediaUserSession, session["oauth_userid_wikimedia"])


@app.route("/logout")
@login_required
def logout():
    """
    A route to log out the user.
    """
    db.session.query(WikimediaUserSession).filter(
        WikimediaUserSession.id == session["oauth_userid_wikimedia"]
    ).delete()
    db.session.commit()

    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("index"))


@app.route("/authorize/wikimedia")
def oauth2_authorize_wikimedia():
    """
    Authorize the user with the Wikimedia APIs.

    This is required to do anything with Flickypedia -- you can't do anything
    unless you're signed into a Wikimedia user who has permission to upload
    files to Commons.
    """
    if not current_user.is_anonymous:
        return redirect(url_for("index"))

    provider_data = app.config["OAUTH2_PROVIDERS"]["wikimedia"]

    # Generate a random string for the state parameter.
    #
    # We'll check this later when we get a callback from Wikimedia --
    # we can use it to maintain state between the request and callback.
    # session["oauth2_state_wikimedia"] = secrets.token_urlsafe(16)

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

    print(provider_data["authorize_url"] + "?" + qs)

    return redirect(provider_data["authorize_url"] + "?" + qs)


@app.route("/callback/wikimedia")
def oauth2_callback_wikimedia():
    """
    Handle an authorization callback from Wikimedia.
    """
    if not current_user.is_anonymous:
        return redirect(url_for("index"))

    provider_data = app.config["OAUTH2_PROVIDERS"]["wikimedia"]

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

    # Store the username in the session.  This isn't sensitive information
    # and is mostly used to render the username in the UI.
    session["wikimedia_user"] = {"id": userinfo["id"], "name": userinfo["name"]}

    # Create a persistent ID for the session.
    session["oauth_userid_wikimedia"] = str(uuid.uuid4())

    user = db.session.scalar(
        db.select(WikimediaUserSession).where(
            WikimediaUserSession.id == session["oauth_userid_wikimedia"]
        )
    )
    if user is None:
        key = Fernet.generate_key()
        session["oauth_key_wikimedia"] = key

        user = WikimediaUserSession(
            id=session["oauth_userid_wikimedia"],
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


with app.app_context():
    db.create_all()
