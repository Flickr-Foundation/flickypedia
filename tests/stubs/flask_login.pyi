from typing import Any, Callable

from flask import Flask
from flask.testing import FlaskClient

from flickypedia.uploadr.auth import WikimediaUserSession

current_user: WikimediaUserSession

def login_required(func: Callable[..., Any]) -> Callable[..., Any]: ...
def login_user(user: WikimediaUserSession) -> None: ...
def logout_user() -> None: ...

class UserMixin: ...

class LoginManager:
    def user_loader(self, callback: Callable[..., Any]) -> Callable[..., Any]: ...
    def init_app(self, app: Flask) -> None: ...

    login_view: str

class FlaskLoginClient(FlaskClient): ...
