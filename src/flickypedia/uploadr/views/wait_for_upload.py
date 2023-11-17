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

from flask import jsonify, redirect, render_template, url_for
from flask_login import login_required

from ..tasks import get_status
from ._types import ViewResponse


@login_required
def wait_for_upload(task_id: str) -> ViewResponse:
    status = get_status(task_id)

    if status["ready"]:
        return redirect(url_for("upload_complete", task_id=task_id))

    return render_template(
        "wait_for_upload.html",
        task_id=task_id,
        current_step="upload_to_wikimedia",
        status=status,
    )


@login_required
def get_upload_status(task_id: str) -> ViewResponse:
    status = get_status(task_id)

    return jsonify(status)
