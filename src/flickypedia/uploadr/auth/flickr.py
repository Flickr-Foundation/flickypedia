import json
import sys
from xml.etree import ElementTree as ET

from authlib.integrations.flask_client import OAuth
from authlib.integrations.httpx_client import OAuth1Client
from authlib.integrations.requests_client import OAuth1Session
from authlib.integrations.requests_client.oauth1_session import OAuth1Auth as ROauth1AuthR
from authlib.integrations.httpx_client.oauth1_client import OAuth1Auth
from authlib.oauth1.rfc5849.client_auth import ClientAuth
import click
from flask import abort, redirect, request, session, url_for
from flask_login import current_user, login_required
import keyring

from requests_oauthlib import OAuth1Session

from flickypedia.types.views import ViewResponse
from flickypedia.utils import (
    find_required_elem,
    find_required_text,
    get_required_password,
)


class FixedClientAuth(ROauth1AuthR):
    def sign(self, method, uri, headers, body):
        from authlib.oauth1.rfc5849.client_auth import generate_nonce, generate_timestamp

        print(f"@@AWLC entering this method {method} {uri} {headers} {body}")
        """Sign the HTTP request, add OAuth parameters and signature.

        :param method: HTTP method of the request.
        :param uri:  URI of the HTTP request.
        :param body: Body payload of the HTTP request.
        :param headers: Headers of the HTTP request.
        :return: uri, headers, body
        """
        nonce = generate_nonce()
        timestamp = generate_timestamp()
        if body is None:
            body = b''

        # transform int to str
        timestamp = str(timestamp)

        if headers is None:
            headers = {}

        oauth_params = self.get_oauth_params(nonce, timestamp)

        # https://datatracker.ietf.org/doc/html/draft-eaton-oauth-bodyhash-00.html
        # include oauth_body_hash
        if body and headers.get('Content-Type') != CONTENT_TYPE_FORM_URLENCODED:
            oauth_body_hash = base64.b64encode(hashlib.sha1(body).digest())
            oauth_params.append(('oauth_body_hash', oauth_body_hash.decode('utf-8')))

        # uri, headers, body = self._render(uri, headers, body, oauth_params)

        sig = self.get_oauth_signature(method, uri, headers, body)
        oauth_params.append(('oauth_signature', sig))

        uri, headers, body = self._render(uri, headers, body, oauth_params)
        return uri, headers, body


class FixedOAuth1Client(OAuth1Client):
    auth_class = FixedClientAuth


class FixedOAuth1Session(OAuth1Session):
    auth_class = FixedClientAuth


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
        next_url = request.args['next_url']
    except KeyError:
        abort(400)

    api_key = get_required_password("flickypedia", "api_key")
    api_secret = get_required_password("flickypedia", "api_secret")

    client = OAuth1Client(
        client_id=api_key, client_secret=api_secret, signature_type="QUERY"
    )

    # Step 1: Getting a Request Token
    #
    # See https://www.flickr.com/services/api/auth.oauth.html#request_token
    #
    redirect_url = url_for('oauth2_callback_flickr', _external=True)

    request_token_resp = client.fetch_request_token(
        url="https://www.flickr.com/services/oauth/request_token",
        params={"oauth_callback":redirect_url }
    )

    request_token = request_token_resp["oauth_token"]

    session['flickr_oauth_next_url'] = next_url
    session['flickr_oauth_request_token'] = json.dumps(request_token_resp)

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
    api_key = get_required_password("flickypedia", "api_key")
    api_secret = get_required_password("flickypedia", "api_secret")

    try:
        request_token = json.loads(session.pop('flickr_oauth_request_token'))
    except ValueError:
        abort(400)

    client = OAuth1Client(
        client_id=api_key,
        client_secret=api_secret,
        token=request_token['oauth_token'],
        token_secret=request_token['oauth_token_secret']
    )

    client.parse_authorization_response(request.url)

    # Step 3: Exchanging the Request Token for an Access Token
    #
    # This token gets saved in the OAuth1Client, so we don't need
    # to inspect the response directly.
    #
    # See https://www.flickr.com/services/api/auth.oauth.html#access_token
    token = client.fetch_access_token(
        url="https://www.flickr.com/services/oauth/access_token"
    )

    # Store the token in our database, so we can access it later, then
    # redirect the user back to the page.
    current_user.store_flickr_oauth_token(token=token)

    try:
        next_url = session.pop('flickr_oauth_next_url')
    except KeyError:
        abort(400)

    return redirect(next_url)
