from typing import Any

class SQLAlchemy:
    Model: Any
    Column: Any
    String: Any
    Integer: Any
    LargeBinary: Any
    DateTime: Any
    session: Any

    def init_app(self, app: Any) -> None: ...
    def create_all(self) -> None: ...
