from collections.abc import Callable
import typing

import httpx

from authlib.oauth2.rfc6749.wrappers import OAuth2Token

class RequestTokenResp(typing.TypedDict):
    oauth_token: str

class OAuth1Client(httpx.Client):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        signature_type: typing.Literal["QUERY"] | None = None,
        token: str | None = None,
        token_secret: str | None = None,
    ) -> None: ...
    def fetch_request_token(
        self, url: str, params: dict[str, str]
    ) -> RequestTokenResp: ...
    def create_authorization_url(self, url: str, request_token: str) -> str: ...
    def fetch_access_token(
        self, url: str, verifier: str | None = None
    ) -> typing.Any: ...
    token: typing.Any
    def parse_authorization_response(self, url: str) -> None: ...

class OAuth2Client(httpx.Client):
    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        authorization_endpoint: str | None = None,
        token_endpoint: str | None = None,
        token: OAuth2Token | None = None,
        update_token: Callable[..., typing.Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None: ...
    token: OAuth2Token
    def ensure_active_token(self, token: OAuth2Token) -> bool: ...
    def create_authorization_url(self, url: str) -> tuple[str, str]: ...
    def fetch_token(
        self, token_endpoint: str, authorization_response: str, state: str
    ) -> OAuth2Token: ...
    def refresh_token(self, url: str) -> None: ...
