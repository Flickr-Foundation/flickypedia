import datetime
from typing import TypedDict

import pytest

from flickypedia.apis.structured_data.wikidata import to_wikidata_date_value
from flickypedia.apis.structured_data._types import DataValueTypes


ToWikidateArgs = TypedDict("ToWikidateArgs", {"d": datetime.datetime, "precision": str})


@pytest.mark.parametrize(
    ["kwargs", "expected"],
    [
        (
            {"d": datetime.datetime(2023, 10, 12, 1, 2, 3), "precision": "day"},
            {
                "value": {
                    "time": "+2023-10-12T00:00:00Z",
                    "precision": 11,
                    "timezone": 0,
                    "before": 0,
                    "after": 0,
                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                },
                "type": "time",
            },
        ),
        (
            {"d": datetime.datetime(2023, 10, 12, 1, 2, 3), "precision": "month"},
            {
                "value": {
                    "time": "+2023-10-00T00:00:00Z",
                    "precision": 10,
                    "timezone": 0,
                    "before": 0,
                    "after": 0,
                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                },
                "type": "time",
            },
        ),
        (
            {"d": datetime.datetime(2023, 10, 12, 1, 2, 3), "precision": "year"},
            {
                "value": {
                    "time": "+2023-00-00T00:00:00Z",
                    "precision": 9,
                    "timezone": 0,
                    "before": 0,
                    "after": 0,
                    "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                },
                "type": "time",
            },
        ),
    ],
)
def test_to_wikidata_date_value(
    kwargs: ToWikidateArgs, expected: DataValueTypes.Time
) -> None:
    assert to_wikidata_date_value(**kwargs) == expected


def test_to_wikidata_date_value_fails_with_unexpected_precision() -> None:
    with pytest.raises(ValueError, match="Unrecognised precision"):
        to_wikidata_date_value(d=datetime.datetime(2023, 10, 12), precision="second")
