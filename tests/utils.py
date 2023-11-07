import json
import re
from typing import Union

from cryptography.fernet import Fernet
from flask import session
from flask_login import login_user

from flickypedia.auth import user_db, WikimediaUserSession, SESSION_ENCRYPTION_KEY
from flickypedia.utils import encrypt_string


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


def store_user(token) -> WikimediaUserSession:
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
    )
    user_db.session.add(user)
    user_db.session.commit()

    login_user(user)

    return user
