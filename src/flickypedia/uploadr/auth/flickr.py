import json
import sys
from xml.etree import ElementTree as ET

from authlib.integrations.httpx_client import OAuth1Client
import click
from flickr_photos_api.utils import find_required_elem, find_required_text
import keyring


def store_flickypedia_user_oauth_token() -> None:
    """
    Get an OAuth 1.0a token for the "Flickypedia" user, and store it
    in the system keychain.

    This token doesn't expire, so once it's stored, it can be used
    to post comments on Flickr as the Flickypedia bot user.

    This follows the procedure described at
    https://www.flickr.com/services/api/auth.oauth.html
    """
    api_key = keyring.get_password("flickypedia", "api_key")
    api_secret = keyring.get_password("flickypedia", "api_secret")

    assert isinstance(api_key, str)
    assert isinstance(api_secret, str)

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
        print(
            "This is only meant to be used to fetch credentials for the flickypedia account!",
            file=sys.stderr,
        )
        sys.exit(1)

    keyring.set_password("flickypedia", "oauth_token", json.dumps(client.token))

    print("Successfully stored an OAuth token for the Flickypedia bot user!")
    print()
    print("You can access this token like so:")
    print()
    print("     import keyring")
    print("     keyring.get_password('flickypedia', 'oauth_token')")
    print()
