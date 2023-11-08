from typing import Any, Callable, Dict, Optional, Tuple

from authlib.oauth2.rfc6749.wrappers import OAuth2Token
import httpx

class OAuth2Client(httpx.Client):
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        authorization_endpoint: Optional[str] = None,
        token_endpoint: Optional[str] = None,
        token: Optional[OAuth2Token] = None,
        update_token: Optional[Callable[..., Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None: ...
    token: OAuth2Token
    def ensure_active_token(self, token: OAuth2Token) -> bool: ...
    def create_authorization_url(self, url: str) -> Tuple[str, str]: ...
    def fetch_token(
        self, token_endpoint: str, authorization_response: str, state: str
    ) -> OAuth2Token: ...
    def refresh_token(self, url: str) -> None: ...
