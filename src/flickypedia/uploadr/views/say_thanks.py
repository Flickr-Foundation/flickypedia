from flask import render_template
from flask_login import login_required

from ..uploads import uploads_queue
from ._types import ViewResponse


def get_completed_task(task_id: str):
    q = uploads_queue()
    task = q.read_task(task_id)

    assert task["state"] == "completed"
    assert all(
        item["state"] in {"succeeded", "failed"}
        for item in task["task_output"].values()
    )

    return task


@login_required
def say_thanks(task_id: str) -> ViewResponse:
    task = get_completed_task(task_id)

    return render_template("say_thanks.html", current_step="say_thanks", task_id=task_id)
