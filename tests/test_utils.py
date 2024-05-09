import datetime
import json
from xml.etree import ElementTree as ET

from cryptography.fernet import Fernet
import pytest

from flickypedia.utils import (
    decrypt_string,
    encrypt_string,
    find_optional_text,
    find_required_elem,
    find_required_text,
)


def test_encryption_can_round_trip() -> None:
    key = Fernet.generate_key()

    plaintext = "my deep dark secret"
    ciphertext = encrypt_string(key, plaintext)
    assert decrypt_string(key, ciphertext) == plaintext


XML = ET.fromstring(
    """
    <?xml version="1.0" encoding="utf-8" ?>
    <greeting>
        <english>Hello world</english>
        <french/>
        <hungarian></hungarian>
    </greeting>""".strip()
)


def test_find_required_elem() -> None:
    english = find_required_elem(XML, path=".//english")
    assert english is not None
    assert english.text == "Hello world"


def test_find_required_elem_throws_if_cannot_find_element() -> None:
    with pytest.raises(ValueError, match="Could not find required match"):
        find_required_elem(XML, path=".//german")


def test_find_required_text() -> None:
    assert find_required_text(XML, path=".//english") == "Hello world"


def test_find_required_text_throws_if_finds_element_without_text() -> None:
    with pytest.raises(ValueError, match="Could not find required text"):
        find_required_text(XML, path=".//french")


def test_find_required_text_throws_if_cannot_find_element() -> None:
    with pytest.raises(ValueError, match="Could not find required match"):
        find_required_text(XML, path=".//german")


@pytest.mark.parametrize(
    ["path", "expected"],
    [
        ("english", "Hello world"),
        ("french", None),
        ("german", None),
        ("hungarian", None),
    ],
)
def test_find_optional_text(path: str, expected: str | None) -> None:
    assert find_optional_text(XML, path=path) == expected
