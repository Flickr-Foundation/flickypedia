import datetime
import json
from typing import Any, Literal, TypedDict, TypeVar
from urllib.parse import quote as urlquote, urlparse
import xml.etree.ElementTree as ET

from cryptography.fernet import Fernet
from flask import render_template, request
import keyring


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


T = TypeVar("T")

EncodedDate = TypedDict(
    "EncodedDate", {"type": Literal["datetime.datetime"], "value": str}
)


class DatetimeEncoder(json.JSONEncoder):
    """
    A custom JSON encoder that supports datetimes.

        >>> t = datetime.datetime(2001, 2, 3, 4, 5, 6)
        >>> json.dumps({"t": t}, cls=DatetimeEncoder)
        '{"t": {"type": "datetime.datetime", "value": "2001-02-03T04:05:06"}}'

    This is meant to be used with ``DatetimeDecoder`` -- together, they
    allow you to serialise a datetime value via JSON and preserve its type.

    """

    def default(self, t: T) -> T | EncodedDate:
        if isinstance(t, datetime.datetime):
            return {"type": "datetime.datetime", "value": t.isoformat()}
        else:  # pragma: no cover
            return t


class DatetimeDecoder(json.JSONDecoder):
    """
    A custom JSON decoder that supports the datetimes encoded
    by DatetimeEncoder.

        >>> json.loads(
        ...     '{"t": {"type": "datetime.datetime", "value": "2001-02-03T04:05:06"}}',
        ...     cls=DatetimeDecoder)
        {'t': datetime.datetime(2001, 2, 3, 4, 5, 6)}

    """

    def __init__(self) -> None:
        super().__init__(object_hook=self.dict_to_object)

    def dict_to_object(self, d: dict[str, Any]) -> dict[str, Any] | datetime.datetime:
        if d.get("type") == "datetime.datetime":
            return datetime.datetime.fromisoformat(d["value"])
        else:
            return d


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


def get_required_password(service_name: str, username: str) -> str:
    """
    Retrieve a password from the keychain, or throw if it's missing.
    """
    password = keyring.get_password(service_name, username)

    if password is None:
        raise RuntimeError(f"Could not retrieve password {(service_name, username)}")

    return password


def find_required_elem(elem: ET.Element, *, path: str) -> ET.Element:
    """
    Find the first subelement matching ``path``, or throw if absent.
    """
    # We use this when we're parsing responses from the Flickr API, and
    # there are certain elements we know should always be present in responses.
    #
    # e.g. we know that photos always have a <title>, so we could write:
    #
    #     photo_elem.find(".//title")
    #
    # But the type checker only knows that ``find()`` returns Optional[Element] --
    # it doesn't know that this path should always be present in the response.
    #
    # If we call it from this function instead:
    #
    #     find_required(photo_elem, path=".//title")
    #
    # Then the type checker can see that it returns a well-defined Element,
    # and it's happy for us to use it without checking in the rest of the code.
    matching_elem = elem.find(path=path)

    if matching_elem is None:
        raise ValueError(f"Could not find required match for {path!r} in {elem!r}")

    return matching_elem


def find_required_text(elem: ET.Element, *, path: str) -> str:
    """
    Find the text of the first element matching ``path``, or throw if absent.
    """
    # We use this when we're parsing responses from the Flickr API, and
    # there are certain elements we know should always be present and have text.
    #
    # e.g. we know that users always have a <id> with some text, so we could write:
    #
    #     user_elem.find(".//id")
    #
    # But the type checker only knows that ``find()`` returns Optional[Element] --
    # it doesn't know that this path should always be present in the response.
    #
    # If we call it from this function instead:
    #
    #     find_required_text(user_elem, path=".//id")
    #
    # Then the type checker can see that it returns a well-defined Element,
    # and it's happy for us to use it without checking in the rest of the code.
    matching_elem = find_required_elem(elem, path=path)
    text = matching_elem.text

    if text is None:
        raise ValueError(f"Could not find required text in {matching_elem}")

    return text


def find_optional_text(elem: ET.Element, *, path: str) -> str | None:
    """
    Find the text of the first element matching ``path``, or return None
    if the element is missing, has no text, or has empty text.
    """
    matching_elem = elem.find(path=path)

    if matching_elem is None:
        return None

    return matching_elem.text or None
