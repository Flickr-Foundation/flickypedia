from flask import abort, render_template, request
from flask_login import login_required

from .upload_complete import get_completed_task
from ._types import ViewResponse


@login_required
def post_comments(task_id: str) -> ViewResponse:
    try:
        user = request.args['user']
    except KeyError:
        abort(400)

    if user not in ('self', 'bot'):
        abort(400)

    task = get_completed_task(task_id)

    successful_requests = []

    for req in task["task_input"]["requests"]:
        photo_id = req["photo"]["id"]

        if task["task_output"][photo_id]["state"] == "succeeded":
            successful_requests.append(req)

    return render_template("post_comments.html", current_step="say_thanks", successful_requests=successful_requests, task=task)
