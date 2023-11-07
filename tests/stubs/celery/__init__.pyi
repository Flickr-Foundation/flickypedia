from typing import Any, Callable, Dict, Type

class Request:
  id: str

class Task:
    def run(self, *args: object, **kwargs: object) -> object: ...
    request: Request

class Celery:
    def __init__(self, name: str, task_cls: Type[Task]) -> None: ...
    def config_from_object(self, config: Dict[str, Any]) -> None: ...
    def set_default(self) -> None: ...

current_task: Task

def shared_task(func: Callable[..., Any]) -> Callable[..., Any]: ...