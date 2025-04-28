"""
A page where a user can track the progress of their upload.

We show them a grid of photos, and the grid gradually updates showing
them the progress.  A photo starts as "not started", then becomes
"in progress", and finally "done" (succeeded) or "not done" (failed).

    +-------------+   +--------------+   +--------------+
    |  ──────▄▀─  |   | ♫░░█▄        |   |   ─▄▀─▄▀     |
    |  ─█▀▀▀█▀█─  |   | ░♫░████▄▄▄▄  |   |   ──▀──▀     |
    |  ──▀▄░▄▀──  |   | ♫░░██▀▀░░░░█ |   |   █▀▀▀▀▀█▄   |
    |  ────█────  |   | ░♫░▀░░▓▓▓▓▀  |   |   █░░░░░█─█  |
    |  ──▄▄█▄▄──  |   | ░░░░▄██████▄ |   |   ▀▄▄▄▄▄▀▀   |
    +-------------+   +--------------+   +--------------+
         done!              done!           not done :(

    +-------------+   +--------------+   +--------------+
    | ─────────▄  |   | ─▄▄██████▄▄─ |   |░░░░░░░░░░░▄██|
    | ───────▄██  |   | ██▀▄█▄▄█▄▀██ |   |░░░░░░░░░▄████|
    | ─▄▀██▀█▀█▀█▀|   | ▀▀▄██▀▀██▄▀▀ |   |░░░░░░░▄██████|
    | ▀▀▀▀▀███▀▀▀ |   | ▄███─██─███▄ |   |░▄██▄▄███▀░██░|
    | ──────▀█    |   | █████▄▄█████ |   |████████▀░░█░░|
    +-------------+   +--------------+   +--------------+
         done!           in progress        not started

The cool ASCII art comes from https://fsymbols.com/text-art/twitter/

== How it works ==

When we render the initial page, we get the current state of the task
and render the grid of photos.  This is a <ul> with an <li> for each
of the photos, and each <li> records the current state in an attribute.

That state attribute defines how the photo gets styled in CSS.

The page gets refreshed periodically:

*   For JS users, there's a JavaScript function on the page that polls
    an API endpoint for retrieving task status.
*   For non-JS users, we use a <meta refresh> tag to force a page
    reload on a schedule.

When the upload completes, we redirect the user to the next page.

"""

import flask
from flask import jsonify, redirect, render_template, url_for
from flask_login import login_required
import werkzeug

from ..uploads import uploads_queue


@login_required
def wait_for_upload(task_id: str) -> str | werkzeug.Response:
    q = uploads_queue()
    task = q.read_task(task_id)

    if task["state"] in {"completed", "failed"}:
        return redirect(url_for("upload_complete", task_id=task_id))

    return render_template(
        "wait_for_upload.html",
        task_id=task_id,
        current_step="upload_to_wikimedia",
        task=task,
    )


@login_required
def get_upload_status(task_id: str) -> flask.Response:
    q = uploads_queue()
    task = q.read_task(task_id)

    return jsonify(
        {
            "state": task["state"],
            "photos": [
                {"photo_id": photo_id, "state": output["state"]}
                for photo_id, output in task["task_output"].items()
            ],
        }
    )
