from flask import render_template
from flask_login import login_required

from flickypedia.tasks import get_status
from ._types import ViewResponse


@login_required
def upload_complete(task_id: str) -> ViewResponse:
    status = get_status(task_id)

    assert status['ready']

    assert all(
        item['status'] in {'succeeded', 'failed'}
        for item in status['progress']
    )

    return render_template("upload_complete.html", status=status, current_step="upload_to_wikimedia")
