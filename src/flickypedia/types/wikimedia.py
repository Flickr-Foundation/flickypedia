import typing


class UserInfo(typing.TypedDict):
    id: str
    name: str


class ShortCaption(typing.TypedDict):
    language: str
    text: str
