from typing import Any, Callable

from flickypedia.auth import WikimediaUserSession

current_user: WikimediaUserSession

def login_required(func: Callable[..., Any]) -> Callable[..., Any]: ...
