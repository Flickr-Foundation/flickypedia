from flask import render_template
from flask_login import login_required

from ..tasks import get_status
from ..uploads import uploads_queue
from ._types import ViewResponse


@login_required
def upload_complete(task_id: str) -> ViewResponse:
    q = uploads_queue()
    task = q.read_task(task_id)

    assert task['state'] in {'completed', 'failed'}
    # assert len(status["progress"]) >= 1
    # assert all(item["status"] in {"succeeded", "failed"} for item in status["progress"])

    successful_requests = []
    failed_requests = []
    upload_results = []

    for req in task['task_input']['requests']:
        photo_id = req['photo']['id']

        if task['task_output'][photo_id]['state'] == 'succeeded':
            successful_requests.append(req)
            upload_results.append(task['task_output'][photo_id])
        else:
            failed_requests.append(req)

    return render_template(
        "upload_complete.html",
        task_id=task_id,
        task=task,
        successful_requests=successful_requests,
        failed_requests=failed_requests,
        upload_results=upload_results,
        current_step="upload_to_wikimedia",
    )
