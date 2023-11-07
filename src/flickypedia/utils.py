import datetime
import json
from typing import Any, Dict, List, Literal, TypedDict, TypeVar, Union
from urllib.parse import quote as urlquote, urlparse

from cryptography.fernet import Fernet
from flask import render_template, request
from flickr_photos_api import Size


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


def size_at(sizes: List[Size], *, desired_size: str) -> Size:
    """
    Given a list of sizes of Flickr photo, return the info about
    the desired size.
    """
    sizes_by_label = {s["label"]: s for s in sizes}

    # Flickr has a published list of possible sizes here:
    # https://www.flickr.com/services/api/misc.urls.html
    #
    # If the desired size isn't available, that means one of two things:
    #
    #   1.  The owner of this photo has done something to restrict downloads
    #       of their photo beyond a certain size.  But CC-licensed photos
    #       are always available to download, so that's not an issue for us.
    #   2.  This photo is smaller than the size we've asked for, in which
    #       case we fall back to Original as the largest possible size.
    #
    try:
        return sizes_by_label[desired_size]
    except KeyError:
        return sizes_by_label["Original"]


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

    def default(self, t: T) -> Union[T, EncodedDate]:
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

    def dict_to_object(
        self, d: Dict[str, Any]
    ) -> Union[Dict[str, Any], datetime.datetime]:
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
