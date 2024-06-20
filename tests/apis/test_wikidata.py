import datetime
import typing

import pytest

from flickypedia.apis.wikidata import get_flickr_user_id
from flickypedia.apis.structured_data.wikidata import to_wikidata_date_value
from flickypedia.types.structured_data import DataValueTypes


ToWikidateArgs = typing.TypedDict(
    "ToWikidateArgs",
    {"d": datetime.datetime, "precision": typing.Literal["day", "month", "year"]},
)


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


@pytest.mark.parametrize(
    ["entity_id", "user_id"], [("Q33132025", "65001151@N03"), ("Q33132026", None)]
)
def test_get_flickr_user_id(
    vcr_cassette: None, entity_id: str, user_id: str | None
) -> None:
    assert get_flickr_user_id(entity_id=entity_id) == user_id
