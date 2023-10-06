from flask import Flask, abort, render_template, redirect, request, url_for
import httpx
import keyring


app = Flask(__name__)

app.config["SECRET_KEY"] = "top secret!"
app.config["OAUTH2_PROVIDERS"] = {
    "wiki": {
        "client_id": keyring.get_password("wiki_s", "client_id"),
        "client_secret": keyring.get_password("wiki_s", "client_secret"),
    }
}


@app.route("/")
def index():
    return render_template(
        "index.html", client_id=app.config["OAUTH2_PROVIDERS"]["wiki"]["client_id"]
    )


@app.route("/callback")
def handle_oauth_callback():
    """
    Handle a redirect from a successful user authorization in step 2 of the
    OAuth 2 user authentication flow.  This is the user being redirected to
    our app's redirect URI as described at the end of [1].

    We're then going to exchange this code for an access token as described in [2].

    [1]: https://api.wikimedia.org/wiki/Authentication#2._Request_authorization
    [2]: https://api.wikimedia.org/wiki/Authentication#3._Get_access_token

    """
    try:
        authorization_code = request.args["code"]
    except KeyError:
        # TODO: Return a better error here, e.g. a page that directs a user back
        # to the beginning of our auth flow.
        abort(400)

    # TODO: Implement better error handling in this function

    resp = httpx.post(
        "https://meta.wikimedia.org/w/rest.php/oauth2/access_token",
        data={
            "grant_type": "authorization_code",
            "code": authorization_code,
            "client_id": app.config["OAUTH2_PROVIDERS"]["wiki"]["client_id"],
            "client_secret": app.config["OAUTH2_PROVIDERS"]["wiki"]["client_secret"],
        },
    )
    resp.raise_for_status()

    from pprint import pprint; pprint(resp.json())
    
    return redirect(url_for("index"))
