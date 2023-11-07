import datetime
import json

from cryptography.fernet import Fernet

from flickypedia.utils import (
    decrypt_string,
    encrypt_string,
    DatetimeDecoder,
    DatetimeEncoder,
)


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
