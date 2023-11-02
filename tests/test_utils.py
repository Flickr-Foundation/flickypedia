import datetime
import json

from cryptography.fernet import Fernet

from flickypedia.utils import (
    decrypt_string,
    encrypt_string,
    size_at,
    DatetimeDecoder,
    DatetimeEncoder,
)


def test_encryption_can_round_trip():
    key = Fernet.generate_key()

    plaintext = "my deep dark secret"
    ciphertext = encrypt_string(key, plaintext)
    assert decrypt_string(key, ciphertext) == plaintext


SIZES = sizes = [
    {
        "label": "Square",
        "width": 75,
        "height": 75,
        "source": "https://live.staticflickr.com/2903/32812033543_c1b3784192_s.jpg",
        "url": "https://www.flickr.com/photos/coast_guard/32812033543/sizes/sq/",
        "media": "photo",
    },
    {
        "label": "Thumbnail",
        "width": 100,
        "height": 61,
        "source": "https://live.staticflickr.com/2903/32812033543_c1b3784192_t.jpg",
        "url": "https://www.flickr.com/photos/coast_guard/32812033543/sizes/t/",
        "media": "photo",
    },
    {
        "label": "Small",
        "width": 240,
        "height": 146,
        "source": "https://live.staticflickr.com/2903/32812033543_c1b3784192_m.jpg",
        "url": "https://www.flickr.com/photos/coast_guard/32812033543/sizes/s/",
        "media": "photo",
    },
    {
        "label": "Original",
        "width": 5172,
        "height": 3145,
        "source": "https://live.staticflickr.com/2903/32812033543_41cc4e453a_o.jpg",
        "url": "https://www.flickr.com/photos/coast_guard/32812033543/sizes/o/",
        "media": "photo",
    },
]


def test_size_at_finds_desired_size():
    assert size_at(SIZES, desired_size="Small") == SIZES[-2]


def test_size_at_falls_back_to_original_if_desired_size_unavailable():
    assert size_at(SIZES, desired_size="Medium") == SIZES[-1]


def test_can_json_round_trip():
    d = {
        "label": "an interesting time",
        "time": datetime.datetime(2001, 2, 3, 4, 5, 6),
    }

    json_string = json.dumps(d, cls=DatetimeEncoder)
    parsed_json_string = json.loads(json_string, cls=DatetimeDecoder)

    assert parsed_json_string == d
