import typing

import pytest
from pydantic import ValidationError

from flickypedia.types import validate_typeddict


class Shape(typing.TypedDict):
    color: str
    sides: int


@pytest.mark.parametrize(
    "data",
    [
        {"color": "red"},
        {"sides": 4},
        {"color": "red", "sides": "four"},
        {"color": (255, 0, 0), "sides": 4},
        {"color": "red", "sides": 4, "angle": 36},
    ],
)
def test_validate_typeddict_flags_incorrect_data(data: typing.Any) -> None:
    with pytest.raises(ValidationError):
        validate_typeddict(data, model=Shape)


def test_validate_typeddict_allows_valid_data() -> None:
    validate_typeddict({"color": "red", "sides": 4}, model=Shape)
