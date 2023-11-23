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
import pathlib
from typing import Any, Literal, TypedDict, Union

from celery import Celery, Task
from celery.result import AsyncResult
from flask import Flask, current_app

from .uploads import PhotoUploadQueue
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
