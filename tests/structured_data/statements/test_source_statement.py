from datetime import datetime

from flickypedia.structured_data.statements import create_source_statement
from utils import get_statement_fixture


def test_create_source_statement() -> None:
    result = create_source_statement(
        photo_id="53248015596",
        photo_url="https://www.flickr.com/photos/199246608@N02/53248015596/",
        original_url="https://live.staticflickr.com/65535/53248015596_c03f8123cf_o_d.jpg",
        retrieved_at=datetime(2023, 11, 14, 16, 15, 0),
    )
    expected = get_statement_fixture(filename="photo_source_data.json")

    assert result == expected


def test_create_source_statement_without_retrieved_at() -> None:
    result = create_source_statement(
        photo_id="53248015596",
        photo_url="https://www.flickr.com/photos/199246608@N02/53248015596/",
        original_url="https://live.staticflickr.com/65535/53248015596_c03f8123cf_o_d.jpg",
        retrieved_at=None,
    )
    expected = get_statement_fixture(filename="photo_source_data_without_date.json")

    assert result == expected
