from flask import render_template
from flask_login import login_required

from ..uploads import uploads_queue
from .say_thanks import get_completed_task
from ._types import ViewResponse


@login_required
def post_comments(task_id: str) -> ViewResponse:
    task = get_completed_task(task_id)

    successful_requests = []

    for req in task["task_input"]["requests"]:
        photo_id = req["photo"]["id"]

        if task["task_output"][photo_id]["state"] == "succeeded":
            successful_requests.append(req)

    return render_template("post_comments.html", current_step="say_thanks", task=task, successful_requests=successful_requests)
