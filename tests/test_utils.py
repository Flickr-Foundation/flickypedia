import datetime
import json
from typing import Any, TypedDict

from cryptography.fernet import Fernet
import keyring
from pydantic import ValidationError
import pytest

from flickypedia.utils import (
    decrypt_string,
    encrypt_string,
    get_required_password,
    validate_typeddict,
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


class Shape(TypedDict):
    color: str
    sides: int


@pytest.mark.parametrize(
    "data",
    [
        {"color": "red"},
        {"sides": 4},
        {"color": "red", "sides": "four"},
        {"color": (255, 0, 0), "sides": 4},
        {"color": "red", "sides": 4, "angle": 36},
    ],
)
def test_validate_typeddict_flags_incorrect_data(data: Any) -> None:
    with pytest.raises(ValidationError):
        validate_typeddict(data, model=Shape)


def test_validate_typeddict_allows_valid_data() -> None:
    validate_typeddict({"color": "red", "sides": 4}, model=Shape)


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
