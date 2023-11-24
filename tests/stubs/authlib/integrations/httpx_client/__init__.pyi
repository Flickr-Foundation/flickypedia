from typing import Any, Literal, TypedDict

import httpx

class RequestTokenResp(TypedDict):
    oauth_token: str

class OAuth1Client:
    def __init__(
        self, client_id: str, client_secret: str, signature_type: Literal["QUERY"]
    ) -> None: ...
    def fetch_request_token(
        self, url: str, params: dict[str, str]
    ) -> RequestTokenResp: ...
    def create_authorization_url(self, url: str, request_token: str) -> str: ...
    def fetch_access_token(self, url: str, verifier: str) -> None: ...
    def get(self, url: str, params: dict[str, str]) -> httpx.Response: ...
    token: Any
