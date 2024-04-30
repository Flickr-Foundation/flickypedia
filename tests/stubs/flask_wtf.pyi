from collections.abc import Iterator
import typing

from wtforms.fields import Field

class Form:
    def validate_on_submit(self) -> bool: ...

class FlaskForm(Form):
    data: dict[str, typing.Any]

    def __iter__(self) -> Iterator[Field]: ...
