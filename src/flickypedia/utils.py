from urllib.parse import quote as urlquote, urlparse

from cryptography.fernet import Fernet
from flask import render_template, request


def encrypt_string(key: bytes, plaintext: str) -> bytes:
    """
    Encrypt an ASCII string using Fernet.
    See https://cryptography.io/en/latest/fernet/#cryptography.fernet.Fernet
    """
    return Fernet(key).encrypt(plaintext.encode("ascii"))


def decrypt_string(key: bytes, ciphertext: bytes) -> str:
    """
    Decode an ASCII string using Fernet.
    See https://cryptography.io/en/latest/fernet/#cryptography.fernet.Fernet
    """
    return Fernet(key).decrypt(ciphertext).decode("ascii")


def create_bookmarklet(filename: str) -> str:
    """
    Create a bookmarklet string, suitable for use in an <a> tag.

    This gets the name of a bookmarklet template in the "templates" folder,
    and returns the rendered and minified JavaScript.
    """
    assert filename.endswith(".js")

    u = urlparse(request.url)
    base_url = f"{u.scheme}://{u.netloc}"

    js = render_template(f"bookmarklets/{filename}", base_url=base_url).strip()
    wrapped_js = """(function() { %s })();""" % js

    return urlquote(wrapped_js)
