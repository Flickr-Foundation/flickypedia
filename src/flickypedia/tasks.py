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


def get_progress(task_id):
    config = Config().CELERY
    in_progress_folder = config["broker_transport_options"]["in_progress_folder"]

    with open(os.path.join(in_progress_folder, f"{task_id}.json")) as in_file:
        return json.load(in_file)


def write_progress(task_id, data):
    config = Config().CELERY
    in_progress_folder = config["broker_transport_options"]["in_progress_folder"]

    with open(os.path.join(in_progress_folder, f"{task_id}.json"), "w") as out_file:
        out_file.write(json.dumps(data))


def get_status(task_id):
    result = AsyncResult(task_id)

    if result.ready():
        return {
            "ready": result.ready(),
            "successful": result.successful(),
            "value": result.result if result.ready() else None,
        }
    else:
        return {"ready": False, "progress": get_progress(task_id)}


@shared_task(ignore_result=False)
def upload_images(count: int) -> int:
    task_id = celery.current_task.request.id

    write_progress(
        task_id=task_id,
        data={"waiting": list(range(count)), "success": [], "failure": []},
    )

    for i in range(count):
        print(f"working on task {celery.current_task.request.id} / image {i}")

        time.sleep(random.uniform(1, 5))

        result = "success" if random.uniform(0, 1) > 0.15 else "failure"

        data = get_progress(task_id)
        data["waiting"].remove(i)
        data[result].append(i)

        write_progress(task_id=task_id, data=data)

    return get_progress(task_id)
