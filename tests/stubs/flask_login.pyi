from typing import Any, Callable

from flask import FlaskClient

from flickypedia.auth import WikimediaUserSession

current_user: WikimediaUserSession

def login_required(func: Callable[..., Any]) -> Callable[..., Any]: ...
def login_user(user: WikimediaUserSession) -> None: ...
def logout_user() -> None: ...

class UserMixin: ...

class LoginManager:
    def user_loader(self, callback: Callable[..., Any]) -> Callable[..., Any]: ...

    login_view: str

class FlaskLoginClient(FlaskClient): ...  # type: ignore
