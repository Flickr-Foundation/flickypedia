from datetime import datetime
import typing

import pytest

from flickypedia.structured_data.types import DataValueTypes, to_wikidata_date_value


ToWikidateArgs = typing.TypedDict(
    "ToWikidateArgs",
    {"d": datetime, "precision": typing.Literal["day", "month", "year"]},
)


@pytest.mark.parametrize(
    ["kwargs", "expected"],
    [
        (
            {"d": datetime(2023, 10, 12, 1, 2, 3), "precision": "day"},
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
            {"d": datetime(2023, 10, 12, 1, 2, 3), "precision": "month"},
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
            {"d": datetime(2023, 10, 12, 1, 2, 3), "precision": "year"},
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
