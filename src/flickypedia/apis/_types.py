from typing import Any, List, Literal, TypedDict, Union


class DateValue(TypedDict):
    time: str
    precision: int
    timezone: int
    before: int
    after: int
    calendarmodel: str


WikidataTime = TypedDict("WikidataTime", {"value": DateValue, "type": Literal["time"]})


class TitleValidationResult:
    Ok = TypedDict("Ok", {"result": Literal["ok"]})
    Failed = TypedDict(
        "Failed",
        {
            "result": Literal["blacklisted", "duplicate", "invalid", "too_long"],
            "text": str,
        },
    )


TitleValidation = Union[TitleValidationResult.Ok, TitleValidationResult.Failed]


class StructuredDataClaims(TypedDict):
    claims: List[Any]
