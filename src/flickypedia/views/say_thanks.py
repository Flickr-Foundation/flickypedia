from flask import render_template
from flask_login import login_required

from flickypedia.tasks import get_status
from ._types import ViewResponse


@login_required
def say_thanks(task_id: str) -> ViewResponse:
    status = get_status(task_id)

    assert status["ready"]
    assert len(status["progress"]) >= 1
    assert all(item["status"] in {"succeeded", "failed"} for item in status["progress"])

    return render_template("say_thanks.html", current_step="say_thanks")
