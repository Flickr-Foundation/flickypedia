from collections.abc import Generator
from typing import Any

from wtforms.fields import Field

class Form:
    def validate_on_submit(self) -> bool: ...

class FlaskForm(Form):
    data: dict[str, Any]

    def __iter__(self) -> Generator[Field, None, None]: ...
