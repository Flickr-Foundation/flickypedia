import os

from flask import Flask, abort, render_template, redirect, request, url_for
from flask_wtf import FlaskForm
import httpx
import keyring
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

from flickypedia.apis.wikimedia import get_userinfo


app = Flask(__name__)

app.config["SECRET_KEY"] = "top secret!"
app.config["OAUTH2_PROVIDERS"] = {
    "wiki": {
        "client_id": keyring.get_password("wiki_s", "client_id"),
        "client_secret": keyring.get_password("wiki_s", "client_secret"),
    }
}


class UploadForm(FlaskForm):
    title = StringField("title", validators=[DataRequired()])
    short_caption = StringField("short_caption", validators=[DataRequired()])
    url = StringField("url", validators=[DataRequired()])
    submit = SubmitField("Upload")


@app.route("/")
def index():
    return render_template(
        "index.html", client_id=app.config["OAUTH2_PROVIDERS"]["wiki"]["client_id"]
    )


# This is a global variable to hold user data.  For obvious reasons, this won't
# be the final storage -- it only allows one logged-in user!
#
# But for early prototyping, it's enough.
ACCESS_TOKEN = {"alex": None}


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

    ACCESS_TOKEN["alex"] = resp.json()
    ACCESS_TOKEN["user_info"] = get_userinfo(access_token=resp.json()["access_token"])

    return redirect(url_for("upload_images"))


@app.route("/upload_images", methods=["GET", "POST"])
def upload_images():
    form = UploadForm()

    if form.validate_on_submit():
        print(form)

        client = httpx.Client(
            headers={"Authorization": f"Bearer {ACCESS_TOKEN['alex']['access_token']}"}
        )

        resp = client.get(
            "https://commons.wikimedia.org/w/api.php",
            params={"action": "query", "meta": "tokens", "format": "json"},
        )

        csrf_token = resp.json()["query"]["tokens"]["csrftoken"]

        print(form.url.data)

        FILE = {
            "file": (
                "SlovenianPlatformWarningSign.jpg",
                open(
                    "/Users/alexwlchan/Desktop/SlovenianPlatformWarningSign.jpg", "rb"
                ),
                "multipart/form-data",
            )
        }

        resp = client.post(
            "https://commons.wikimedia.org/w/api.php",
            files=FILE,
            data={
                "action": "upload",
                "filename": "SlovenianPlatformWarningSign.jpg",
                "format": "json",
                "token": csrf_token,
                #     "ignorewarnings": 1
            },
        )
        print(resp)
        #
        # R = S.post(URL, data=PARAMS_4))

        from pprint import pprint

        pprint(resp.json())

    return render_template("upload_images.html", user_info={}, form=form)
