import typing


class UserInfo(typing.TypedDict):
    id: str
    name: str


class ShortCaption(typing.TypedDict):
    language: str
    text: str


class TitleValidationResult:
    Ok = typing.TypedDict("Ok", {"result": typing.Literal["ok"]})
    Failed = typing.TypedDict(
        "Failed",
        {
            "result": typing.Literal["blacklisted", "duplicate", "invalid", "too_long"],
            "text": str,
        },
    )


TitleValidation = TitleValidationResult.Ok | TitleValidationResult.Failed
