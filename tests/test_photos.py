from flickypedia.photos import size_at
from flickypedia.types.flickr import Size


SIZES: list[Size] = [
    {
        "label": "Square",
        "width": 75,
        "height": 75,
        "source": "https://live.staticflickr.com/2903/32812033543_c1b3784192_s.jpg",
        "media": "photo",
    },
    {
        "label": "Thumbnail",
        "width": 100,
        "height": 61,
        "source": "https://live.staticflickr.com/2903/32812033543_c1b3784192_t.jpg",
        "media": "photo",
    },
    {
        "label": "Small",
        "width": 240,
        "height": 146,
        "source": "https://live.staticflickr.com/2903/32812033543_c1b3784192_m.jpg",
        "media": "photo",
    },
    {
        "label": "Original",
        "width": 5172,
        "height": 3145,
        "source": "https://live.staticflickr.com/2903/32812033543_41cc4e453a_o.jpg",
        "media": "photo",
    },
]


def test_size_at_finds_desired_size() -> None:
    assert size_at(SIZES, desired_size="Small") == SIZES[-2]


def test_size_at_falls_back_to_original_if_desired_size_unavailable() -> None:
    assert size_at(SIZES, desired_size="Medium") == SIZES[-1]
