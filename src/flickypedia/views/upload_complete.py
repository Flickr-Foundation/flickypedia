from flask import render_template
from flask_login import login_required

from flickypedia.tasks import get_status
from ._types import ViewResponse


@login_required
def upload_complete(task_id: str) -> ViewResponse:
    status = get_status(task_id)

    assert status["ready"]
    assert len(status['progress']) >= 1
    assert all(item["status"] in {"succeeded", "failed"} for item in status["progress"])

    successful_requests = [s for s in status["progress"] if s["status"] == "succeeded"]
    failed_requests = [s for s in status["progress"] if s["status"] == "failed"]

    return render_template(
        "upload_complete.html",
        task_id=task_id,
        successful_requests=successful_requests,
        failed_requests=failed_requests,
        current_step="upload_to_wikimedia",
    )
