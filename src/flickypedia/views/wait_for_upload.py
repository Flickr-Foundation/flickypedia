from flask import jsonify, render_template
from flask_login import login_required

from flickypedia.tasks import get_status
from ._types import ViewResponse


@login_required
def wait_for_upload(task_id: str) -> ViewResponse:
    return render_template(
        "wait_for_upload.html", task_id=task_id, current_step="upload_to_wikimedia"
    )


@login_required
def get_upload_status(task_id: str) -> ViewResponse:
    status = get_status(task_id)

    return jsonify(status)
