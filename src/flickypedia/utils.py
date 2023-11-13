import datetime
import itertools
import json
from typing import (
    Any,
    Dict,
    Generator,
    Iterable,
    Literal,
    Tuple,
    TypedDict,
    TypeVar,
    Union,
)
from urllib.parse import quote as urlquote, urlparse

from cryptography.fernet import Fernet
from flask import render_template, request
from pydantic import ConfigDict, TypeAdapter


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


def chunked_iterable(
    iterable: Iterable[T], *, size: int
) -> Generator[Tuple[T, ...], None, None]:
    """
    Break an iterable into fixed-size pieces.

        >>> chunked_iterable(range(14), size=4):
        (0, 1, 2, 3)
        (4, 5, 6, 7)
        (8, 9, 10, 11)
        (12, 13)
        (0, 1, 2)

    """
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, size))
        if not chunk:
            break
        yield chunk


def validate_typeddict(t: Any, model: type[T]) -> T:
    """
    Check that some data matches a TypedDict.

    We use this to check that the structured data we receive
    from Wikimedia matches our definitions, so we can use it
    in type-checked Python.

    See https://stackoverflow.com/a/77386216/1558022
    """
    model.__pydantic_config__ = ConfigDict(extra="forbid")  # type: ignore
    TypedDictValidator = TypeAdapter(model)
    return TypedDictValidator.validate_python(t, strict=True)
