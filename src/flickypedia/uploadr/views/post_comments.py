import json

import flask
from flask import abort, jsonify, render_template, request, url_for
from flask_login import current_user, login_required
from flickr_api import FlickrApi
import werkzeug

from .upload_complete import get_completed_task


@login_required
def post_comments(task_id: str) -> str | werkzeug.Response:
    try:
        user = request.args["user"]
    except KeyError:
        abort(400)

    if user not in ("self", "bot"):
        abort(400)

    task = get_completed_task(task_id)

    successful_requests = []

    for req in task["task_input"]["requests"]:
        photo_id = req["photo"]["id"]

        if task["task_output"][photo_id]["state"] == "succeeded":
            successful_requests.append(req)

    return render_template(
        "post_comments.html",
        current_step="say_thanks",
        successful_requests=successful_requests,
        user=user,
        task=task,
        api_urls={
            "bot_comment": url_for("post_bot_comment_api"),
            "user_comment": url_for("post_user_comment_api"),
        },
    )


@login_required
def post_bot_comment_api() -> flask.Response:
    from flickypedia.apis.flickr.comments import post_bot_comment

    assert request.method == "POST"

    try:
        task_id = request.args["task_id"]
        photo_id = request.args["photo_id"]
    except KeyError:
        abort(400)

    task = get_completed_task(task_id)
    output = task["task_output"][photo_id]

    if output["state"] != "succeeded":
        abort(400)

    assert output["state"] == "succeeded"
    wikimedia_page_title = output["title"]

    try:
        comment_id = post_bot_comment(
            user_name=current_user.name,
            user_url=current_user.profile_url,
            photo_id=photo_id,
            wikimedia_page_title=wikimedia_page_title,
        )

        return jsonify({"comment_id": comment_id})
    except Exception as exc:
        return jsonify({"error": str(exc)})


@login_required
def post_user_comment_api() -> flask.Response | werkzeug.Response:
    assert request.method == "POST"

    try:
        task_id = request.args["task_id"]
        photo_id = request.args["photo_id"]
        comment_text = json.loads(request.data)
    except KeyError:
        abort(400)

    task = get_completed_task(task_id)
    output = task["task_output"][photo_id]

    if output["state"] != "succeeded":
        abort(400)

    assert output["state"] == "succeeded"

    client = current_user.flickr_oauth_client()
    api = FlickrApi(client=client)

    try:
        comment_id = api.post_comment(photo_id=photo_id, comment_text=comment_text)

        return jsonify({"comment_id": comment_id})
    except Exception as exc:
        raise
        print(exc)
        return jsonify({"error": str(exc)})
