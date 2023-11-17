import datetime
import json
import os
import re
from typing import TypeVar, Union

from authlib.oauth2.rfc6749.wrappers import OAuth2Token
from cryptography.fernet import Fernet
from flask import session
from flask_login import login_user

from flickypedia.uploadr.auth import (
    user_db,
    WikimediaUserSession,
    SESSION_ENCRYPTION_KEY,
)
from flickypedia.utils import DatetimeDecoder, encrypt_string, validate_typeddict


T = TypeVar("T")


def minify(text: Union[str, bytes]) -> str:
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


def store_user(token: OAuth2Token) -> WikimediaUserSession:
    """
    Create a user and store them in the database.
    """
    key = Fernet.generate_key()

    session[SESSION_ENCRYPTION_KEY] = key

    user = WikimediaUserSession(
        id="example",
        userid="-1",
        name="example",
        encrypted_token=encrypt_string(key, plaintext=json.dumps(token)),
        first_login=datetime.datetime.now(),
    )
    user_db.session.add(user)
    user_db.session.commit()

    login_user(user)

    return user


def get_typed_fixture(path: str, model: type[T]) -> T:
    """
    Read a JSON fixture from the ``tests/fixtures`` directory.

    This function will validate that the JSON fixture matches the
    specified model.
    """
    with open(os.path.join("tests/fixtures", path)) as f:
        return validate_typeddict(json.load(f, cls=DatetimeDecoder), model)
