import datetime
import json
from xml.etree import ElementTree as ET

from cryptography.fernet import Fernet
import keyring
import pytest

from flickypedia.utils import (
    decrypt_string,
    encrypt_string,
    find_optional_text,
    find_required_elem,
    find_required_text,
    get_required_password,
    DatetimeDecoder,
    DatetimeEncoder,
)
from utils import InMemoryKeyring


def test_encryption_can_round_trip() -> None:
    key = Fernet.generate_key()

    plaintext = "my deep dark secret"
    ciphertext = encrypt_string(key, plaintext)
    assert decrypt_string(key, ciphertext) == plaintext


def test_can_json_round_trip() -> None:
    d = {
        "label": "an interesting time",
        "time": datetime.datetime(2001, 2, 3, 4, 5, 6),
    }

    json_string = json.dumps(d, cls=DatetimeEncoder)
    parsed_json_string = json.loads(json_string, cls=DatetimeDecoder)

    assert parsed_json_string == d


class TestGetRequiredPassword:
    def test_gets_existing_password(self) -> None:
        keyring.set_keyring(
            InMemoryKeyring(passwords={("flickypedia", "api_key"): "12345"})
        )

        assert get_required_password("flickypedia", "api_key") == "12345"

    def test_throws_if_password_does_not_exist(self) -> None:
        keyring.set_keyring(InMemoryKeyring(passwords={}))

        with pytest.raises(RuntimeError, match="Could not retrieve password"):
            get_required_password("flickypedia", "api_key")


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
