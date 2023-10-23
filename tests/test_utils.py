from cryptography.fernet import Fernet
import pytest

from flickypedia.utils import decrypt_string, encrypt_string, size_at


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
]


def test_size_at_finds_desired_size():
    assert size_at(SIZES, desired_size="Small") == SIZES[-1]


def test_size_at_fails_if_no_desired_size():
    with pytest.raises(
        ValueError, match="This photo is not available at size 'Medium'"
    ):
        size_at(SIZES, desired_size="Medium")
