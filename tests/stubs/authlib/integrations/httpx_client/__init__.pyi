from typing import Any, Literal, TypedDict

import httpx

class RequestTokenResp(TypedDict):
    oauth_token: str

class OAuth1Client(httpx.Client):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        signature_type: Literal["QUERY"] | None = None,
        token: str | None = None,
        token_secret: str | None = None,
    ) -> None: ...
    def fetch_request_token(
        self, url: str, params: dict[str, str]
    ) -> RequestTokenResp: ...
    def create_authorization_url(self, url: str, request_token: str) -> str: ...
    def fetch_access_token(self, url: str, verifier: str | None = None) -> Any: ...
    token: Any
    def parse_authorization_response(self, url: str) -> None: ...
