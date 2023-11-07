from typing import Any, Dict

class Form:
    def validate_on_submit(self) -> bool: ...

class FlaskForm(Form):
    data: Dict[str, Any]
