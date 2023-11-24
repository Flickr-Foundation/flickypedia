from collections.abc import Callable
from typing import Any

from authlib.oauth2.rfc6749.wrappers import OAuth2Token
import httpx

class OAuth2Client(httpx.Client):
    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        authorization_endpoint: str | None = None,
        token_endpoint: str | None = None,
        token: OAuth2Token | None = None,
        update_token: Callable[..., Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None: ...
    token: OAuth2Token
    def ensure_active_token(self, token: OAuth2Token) -> bool: ...
    def create_authorization_url(self, url: str) -> tuple[str, str]: ...
    def fetch_token(
        self, token_endpoint: str, authorization_response: str, state: str
    ) -> OAuth2Token: ...
    def refresh_token(self, url: str) -> None: ...
