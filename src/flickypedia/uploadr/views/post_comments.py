from flask import abort, jsonify, render_template, request, url_for
from flask_login import current_user, login_required

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

    return render_template(
        "post_comments.html",
        current_step="say_thanks",
        task=task,
        successful_requests=successful_requests,
        api_url=url_for("post_bot_comment_api")
    )


@login_required
def post_bot_comment_api() -> ViewResponse:
    from flickypedia.apis.flickr.comments import post_bot_comment

    assert request.method == "POST"

    try:
        task_id = request.args["task_id"]
        photo_id = request.args["photo_id"]
    except KeyError:
        abort(400)

    task = get_completed_task(task_id)

    if task["task_output"][photo_id]["state"] != "succeeded":
        abort(400)

    wikimedia_page_title = task["task_output"][photo_id]["title"]

    comment_id = post_bot_comment(user=current_user, photo_id=photo_id, wikimedia_page_title=wikimedia_page_title)

    return jsonify({"comment_id": comment_id})
