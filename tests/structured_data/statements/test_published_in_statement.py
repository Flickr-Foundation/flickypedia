from datetime import datetime

from flickypedia.structured_data.statements import create_published_in_statement
from utils import get_statement_fixture


def test_create_published_in_statement() -> None:
    actual = create_published_in_statement(date_posted=datetime(2023, 10, 12))
    expected = get_statement_fixture(filename="date_posted_to_flickr.json")

    assert actual == expected
