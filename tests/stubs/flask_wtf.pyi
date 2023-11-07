from typing import Any, Dict, Generator

from wtforms.fields import Field

class Form:
    def validate_on_submit(self) -> bool: ...

class FlaskForm(Form):
    data: Dict[str, Any]

    def __iter__(self) -> Generator[Field, None, None]: ...
