from typing import Optional, TypedDict


class FlickrUser(TypedDict):
    id: str
    username: str
    realname: Optional[str]
