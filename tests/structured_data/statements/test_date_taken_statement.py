from datetime import datetime, timezone

from flickr_api.models import TakenGranularity
import pytest

from flickypedia.structured_data.statements import create_date_taken_statement
from utils import get_statement_fixture


@pytest.mark.parametrize(
    ["date_taken", "granularity", "filename"],
    [
        # Based on https://www.flickr.com/photos/184374196@N07/53069446440
        (
            datetime(2023, 2, 20, 23, 32, 31),
            "second",
            "date_taken_YYYY-MM-DD.json",
        ),
        # Based on https://www.flickr.com/photos/normko/361850789
        (datetime(1970, 3, 1, 0, 0, 0), "month", "date_taken_YYYY-MM.json"),
        # Based on https://www.flickr.com/photos/nationalarchives/5240741057
        (datetime(1950, 1, 1, 0, 0, 0), "year", "date_taken_YYYY.json"),
        # Based on https://www.flickr.com/photos/nlireland/6975991819
        (datetime(1910, 1, 1, 0, 0, 0), "circa", "date_taken_circa.json"),
    ],
)
def test_create_date_taken_statement(
    date_taken: datetime, granularity: TakenGranularity, filename: str
) -> None:
    actual = create_date_taken_statement(
        date_taken={"value": date_taken, "granularity": granularity}
    )
    expected = get_statement_fixture(filename)

    assert actual == expected


def test_create_date_taken_statement_fails_on_unrecognised_granularity() -> None:
    with pytest.raises(ValueError, match="Unrecognised taken_granularity"):
        create_date_taken_statement(
            date_taken={
                "value": datetime.now(tz=timezone.utc),
                "granularity": -1,  # type: ignore
                "unknown": False,
            }
        )
