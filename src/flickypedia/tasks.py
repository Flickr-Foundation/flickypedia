"""
All of Flickypedia's uploads happen in a task queue managed by Celery.

Currently Celery stores all its config in the local filesystem, rather
than an external broker like Redis/Memcached.  We could look at using
those systems later if we need something with more throughput -- it
depends on our deployment options, and I'd rather avoid an external
dependency if I can help it.

== Progress tracking ==

If you use Celery out of the box, you just get a "success/fail" response
when the entire task is done.

To provide a better experience to users, we have two functions:

*   record_progress()
*   get_progress()

which can be used to report progress updates as you're going along.

== Useful background reading ==

*   Background tasks with Celery
    https://flask.palletsprojects.com/en/2.3.x/patterns/celery/

"""

import json
import os
from typing import Any, Literal, TypedDict, Union

from celery import Celery, Task
from celery.result import AsyncResult
from flask import Flask, current_app

from flickypedia.utils import DatetimeDecoder, DatetimeEncoder


def celery_init_app(app: Flask) -> Celery:
    """
    Create and configure the Celery app.

    This is based on an example from the Flask docs.
    See https://flask.palletsprojects.com/en/2.3.x/patterns/celery/#integrate-celery-with-flask
    """

    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)

    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


class ProgressTracker:
    def __init__(self, task_id: str) -> None:
        self.task_id = task_id

    @property
    def path(self) -> str:
        """
        Returns the path to a file which can be used for tracking information
        about an in-progress task.
        """
        config = current_app.config["CELERY"]
        in_progress_folder = config["broker_transport_options"]["in_progress_folder"]

        return os.path.join(in_progress_folder, f"{self.task_id}.json")

    def record_progress(self, data: Any) -> None:
        """
        Records the state of an in-progress task.
        """
        with open(self.path, "w") as out_file:
            out_file.write(json.dumps(data, cls=DatetimeEncoder))

    def get_progress(self) -> Any:
        """
        Retrieves the state of an in-progress task.
        """
        try:
            with open(self.path) as in_file:
                return json.load(in_file, cls=DatetimeDecoder)
        except FileNotFoundError:
            return None


class SuccessfulStatus(TypedDict):
    ready: Literal[True]
    successful: bool
    value: Any


class PendingStatus(TypedDict):
    ready: Literal[False]
    progress: Any


def get_status(task_id: str) -> Union[SuccessfulStatus, PendingStatus]:
    """
    Retrieve the status of a Celery task.
    """
    result = AsyncResult(task_id)

    if result.ready():
        return {
            "ready": True,
            "successful": result.successful(),
            "value": result.result if result.ready() else None,
        }
    else:
        return {
            "ready": False,
            "value": ProgressTracker(task_id=task_id).get_progress(),
        }
