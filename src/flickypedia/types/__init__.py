from typing import TypedDict


class FlickrOAuthToken(TypedDict):
    fullname: str | None
    oauth_token: str
    oauth_token_secret: str
    user_nsid: str
    username: str
