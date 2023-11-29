from typing import Literal, TypedDict


class UserInfo(TypedDict):
    id: str
    name: str


class ShortCaption(TypedDict):
    language: str
    text: str


class TitleValidationResult:
    Ok = TypedDict("Ok", {"result": Literal["ok"]})
    Failed = TypedDict(
        "Failed",
        {
            "result": Literal["blacklisted", "duplicate", "invalid", "too_long"],
            "text": str,
        },
    )


TitleValidation = TitleValidationResult.Ok | TitleValidationResult.Failed
