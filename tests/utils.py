import datetime
import json
import pathlib
import re
import typing

from authlib.oauth2.rfc6749.wrappers import OAuth2Token
from cryptography.fernet import Fernet
from flask.testing import FlaskClient
from flask_login import login_user
from nitrate.json import DatetimeDecoder

from flickypedia.uploadr.auth import (
    user_db,
    WikimediaUserSession,
    SESSION_ENCRYPTION_KEY,
)
from flickypedia.types import validate_typeddict, Path
from flickypedia.utils import encrypt_string


T = typing.TypeVar("T")


def minify(text: str | bytes) -> str:
    """
    Minify an HTML string.  This means compacting long runs of whitespace,
    e.g.

        >>> html = "this album\n is created\n from a Jinja2 template"
        >>> "this album is created" in html
        False
        >>> "this album is created" in minify(html)
        True

    It's meant for use in tests -- this may not be a perfect minifier,
    but it's good enough for our test assertions.
    """
    if isinstance(text, bytes):
        text = text.decode("utf8")

    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text


def store_user(
    client: FlaskClient, token: OAuth2Token | None = None
) -> WikimediaUserSession:
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

    with client.session_transaction() as session:
        session[SESSION_ENCRYPTION_KEY] = key

    # (I haven't actually checked this, but I'm pretty sure user IDs
    # in Wikimedia are all positive integers.)
    user = WikimediaUserSession(
        id="-3",
        userid="-3",
        name="FlickypediaTestingUser",
        encrypted_token=encrypt_string(key, plaintext=json.dumps(oauth2_token)),
        first_login=datetime.datetime.now(),
    )
    user_db.session.add(user)
    user_db.session.commit()

    login_user(user)

    return user


def get_typed_fixture(path: Path, model: type[T]) -> T:
    """
    Read a JSON fixture from the ``tests/fixtures`` directory.

    This function will validate that the JSON fixture matches the
    specified model.
    """
    fixtures_dir = pathlib.Path("tests/fixtures")

    with open(fixtures_dir / path) as f:
        return validate_typeddict(json.load(f, cls=DatetimeDecoder), model)
