import json
import sys
from xml.etree import ElementTree as ET

from authlib.integrations.httpx_client import OAuth1Client
import click
from flask import abort, current_app, redirect, request, session, url_for
from flask_login import current_user, login_required
import keyring

from flickypedia.types.views import ViewResponse
from flickypedia.utils import (
    find_required_elem,
    find_required_text,
    get_required_password,
)


def store_flickypedia_user_oauth_token() -> None:
    """
    Get an OAuth 1.0a token for the "Flickypedia" user, and store it
    in the system keychain.

    This token doesn't expire, so once it's stored, it can be used
    to post comments on Flickr as the Flickypedia bot user.

    This follows the procedure described at
    https://www.flickr.com/services/api/auth.oauth.html
    """
    api_key = get_required_password("flickypedia", "api_key")
    api_secret = get_required_password("flickypedia", "api_secret")

    client = OAuth1Client(
        client_id=api_key, client_secret=api_secret, signature_type="QUERY"
    )

    # Step 1: Getting a Request Token
    #
    # Note: "oob" in the OAuth callback stands for "out-of-band".
    # Normally when you authenticate with the Flickr API, you send the
    # user to a URL to authorize your app, then they get redirected back
    # to your web app with an authorization code.
    #
    # But we aren't running a web server to be redirected to -- instead,
    # using "oob" means we'll be shown a verification code we need
    # to type in later.
    #
    # See https://www.flickr.com/services/api/auth.oauth.html#request_token
    #
    request_token_resp = client.fetch_request_token(
        url="https://www.flickr.com/services/oauth/request_token",
        params={"oauth_callback": "oob"},
    )

    request_token = request_token_resp["oauth_token"]

    # Step 2: Getting the User Authorization
    #
    # This creates an authorization URL on flickr.com, where the user
    # can choose to authorize the app (or not).
    #
    # See https://www.flickr.com/services/api/auth.oauth.html#request_token
    authorization_url = client.create_authorization_url(
        url="https://www.flickr.com/services/oauth/authorize",
        request_token=request_token,
    )

    print("Please open the following URL in your web browser:")
    print(authorization_url)
    print()

    print(
        "You'll be asked to authorize the 'Flickypedia comments' app, then shown a verification code."
    )

    verifier = click.prompt("Please enter that code here")

    # Step 3: Exchanging the Request Token for an Access Token
    #
    # This token gets saved in the OAuth1Client, so we don't need
    # to inspect the response directly.
    #
    # See https://www.flickr.com/services/api/auth.oauth.html#access_token
    client.fetch_access_token(
        url="https://www.flickr.com/services/oauth/access_token", verifier=verifier
    )

    # At this point we have an OAuth token for this user.
    #
    # As an additional safety step, we call the flickr.test.login API
    # to get details on this user -- this should only ever be called
    # for the Flickypedia Bot user.
    login_resp = client.get(
        "https://www.flickr.com/services/rest", params={"method": "flickr.test.login"}
    )

    xml = ET.fromstring(login_resp.text)

    user_id = find_required_elem(xml, path=".//user").attrib["id"]
    username = find_required_text(xml, path=".//username")

    if user_id != "199561775@N05" or username != "flickypedia":
        print()
        print(
            "This is only meant to be used to fetch credentials for the Flickypedia bot account!",
            file=sys.stderr,
        )
        print(f"You logged in as {username!r}!", file=sys.stderr)
        sys.exit(1)

    keyring.set_password("flickypedia.bot", "oauth_token", json.dumps(client.token))

    print("Successfully stored an OAuth token for the Flickypedia bot user!")
    print()
    print("You can access this token like so:")
    print()
    print("     import keyring")
    print("     keyring.get_password('flickypedia.bot', 'oauth_token')")
    print()


def get_flickypedia_bot_oauth_client() -> OAuth1Client:
    """
    Creates an OAuth1Client which is authorised to post comments to the
    Flickr API as the Flickypedia bot user.
    """
    api_key = get_required_password("flickypedia", "api_key")
    api_secret = get_required_password("flickypedia", "api_secret")
    stored_token = json.loads(get_required_password("flickypedia.bot", "oauth_token"))

    client = OAuth1Client(
        client_id=api_key,
        client_secret=api_secret,
        signature_type="QUERY",
        token=stored_token["oauth_token"],
        token_secret=stored_token["oauth_token_secret"],
    )

    return client


@login_required
def oauth2_authorize_flickr() -> ViewResponse:
    """
    Authorize the user with the Flickr APIs.

    This is a named route which redirects so we can access it
    with ``url_for()`` in templates.
    """
    # Where should the user be redirected when they've logged into Flickr?
    try:
        next_url = request.args["next_url"]
    except KeyError:
        abort(400)

    # If the user is already logged in to Flickr, we don't need to send
    # them back through Flickr's OAuth flow -- the tokens we get don't
    # expire, so we can presume they're still good.
    if current_user.encrypted_flickr_token is not None:
        return redirect(next_url)

    oauth_config = current_app.config["OAUTH_PROVIDERS"]["flickr"]

    client = OAuth1Client(
        client_id=oauth_config["client_id"],
        client_secret=oauth_config["client_secret"],
        signature_type="QUERY",
    )

    # Step 1: Getting a Request Token
    #
    # See https://www.flickr.com/services/api/auth.oauth.html#request_token
    #
    # Note: we could put the next_url parameter in here, but this
    # causes issues with the OAuth 1.0a signatures, so I'm passing that
    # in the Flask session instead.
    redirect_url = url_for("oauth2_callback_flickr", _external=True)

    request_token_resp = client.fetch_request_token(
        url=oauth_config["request_url"],
        params={"oauth_callback": redirect_url},
    )

    request_token = request_token_resp["oauth_token"]

    session["flickr_oauth_next_url"] = next_url
    session["flickr_oauth_request_token"] = json.dumps(request_token_resp)

    # Step 2: Getting the User Authorization
    #
    # This creates an authorization URL on flickr.com, where the user
    # can choose to authorize the app (or not).
    #
    # See https://www.flickr.com/services/api/auth.oauth.html#request_token
    authorization_url = client.create_authorization_url(
        url="https://www.flickr.com/services/oauth/authorize",
        request_token=request_token,
    )

    return redirect(authorization_url)


@login_required
def oauth2_callback_flickr() -> ViewResponse:
    """
    Handle an authorization callback from Flickr.
    """
    oauth_config = current_app.config["OAUTH_PROVIDERS"]["flickr"]

    try:
        request_token = json.loads(session.pop("flickr_oauth_request_token"))
    except (KeyError, ValueError):
        abort(400)

    client = OAuth1Client(
        client_id=oauth_config["client_id"],
        client_secret=oauth_config["client_secret"],
        token=request_token["oauth_token"],
        token_secret=request_token["oauth_token_secret"],
    )

    client.parse_authorization_response(request.url)

    # Step 3: Exchanging the Request Token for an Access Token
    #
    # This token gets saved in the OAuth1Client, so we don't need
    # to inspect the response directly.
    #
    # See https://www.flickr.com/services/api/auth.oauth.html#access_token
    token = client.fetch_access_token(url=oauth_config["token_url"])

    # Store the token in our database, so we can access it later, then
    # redirect the user back to the page.
    current_user.store_flickr_oauth_token(token=token)

    try:
        next_url = session.pop("flickr_oauth_next_url")
    except KeyError:
        abort(400)

    return redirect(next_url)
