import datetime
from typing import Optional, TypedDict


class DateTaken(TypedDict):
    value: datetime.datetime
    granularity: int
    unknown: bool


class FlickrUser(TypedDict):
    id: str
    username: str
    realname: Optional[str]
