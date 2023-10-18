"""
All of Flickypedia's uploads happen in a task queue managed by Celery.

Currently Celery stores all its config in the local filesystem, rather
than an external broker like Redis/Memcached.  We could look at using
those systems later if we need something with more throughput -- it
depends on our deployment options, and I'd rather avoid an external
dependency if I can help it.

This file has some generic utilities related to task management.

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
import random
import time

import celery
from celery import Celery, shared_task
from celery.result import AsyncResult
from flask import Flask

from flickypedia.config import Config


def celery_init_app(app: Flask) -> Celery:
    """
    Create and configure the Celery app.

    This is based on an example from the Flask docs.
    See https://flask.palletsprojects.com/en/2.3.x/patterns/celery/#integrate-celery-with-flask
    """
    celery_app = Celery(app.name)

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


class ProgressTracker:
    def __init__(self, task_id):
        self.task_id = task_id

    @property
    def path(self):
        """
        Returns the path to a file which can be used for tracking information
        about an in-progress task.
        """
        config = Config().CELERY
        in_progress_folder = config["broker_transport_options"]["in_progress_folder"]

        return os.path.join(in_progress_folder, f"{self.task_id}.json")

    def record_progress(self, data):
        """
        Records the state of an in-progress task.
        """
        with open(self.path, "w") as out_file:
            out_file.write(json.dumps(data))

    def get_progress(self):
        """
        Retrieves the state of an in-progress task.
        """
        try:
            with open(self.path) as in_file:
                return json.load(in_file)
        except FileNotFoundError:
            return


def get_status(task_id):
    """
    Retrieve the status of a Celery task.
    """
    result = AsyncResult(task_id)

    if result.ready():
        return {
            "ready": result.ready(),
            "successful": result.successful(),
            "value": result.result if result.ready() else None,
        }
    else:
        return {
            "ready": False,
            "progress": ProgressTracker(task_id=task_id).get_progress(),
        }


@shared_task(ignore_result=False)
def upload_images(count: int) -> int:
    tracker = ProgressTracker(task_id=celery.current_task.request.id)

    tracker.record_progress(
        data={"waiting": list(range(count)), "success": [], "failure": []},
    )

    for i in range(count):
        print(f"working on task {celery.current_task.request.id} / image {i}")

        time.sleep(random.uniform(1, 5))

        result = "success" if random.uniform(0, 1) > 0.15 else "failure"

        data = tracker.get_progress()
        data["waiting"].remove(i)
        data[result].append(i)

        tracker.record_progress(data=data)

    return tracker.get_progress()
