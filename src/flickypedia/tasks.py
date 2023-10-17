"""
All of Flickypedia's uploads happen in a task queue managed by Celery.

Currently Celery stores all its config in the local filesystem, rather
than an external broker like Redis/Memcached.  We could look at using
those systems later if we need something with more throughput -- it
depends on our deployment options, and I'd rather avoid an external
dependency if I can help it.

== Useful background reading ==

*   Background tasks with Celery
    https://flask.palletsprojects.com/en/2.3.x/patterns/celery/

"""

import os

from celery import Celery, Task
from flask import Flask


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

    config = app.config["CELERY"]

    # Ensure that all the folders that Celery requires are created before
    # it starts -- Celery won't create them itself.
    for dirname in [
        config["result_backend"].replace("file://", ""),
        config["broker_transport_options"]["data_folder_in"],
        config["broker_transport_options"]["data_folder_out"],
        config["broker_transport_options"]["processed_folder"],
        config["broker_transport_options"]["in_progress_folder"],
    ]:
        os.makedirs(dirname, exist_ok=True)

    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app
