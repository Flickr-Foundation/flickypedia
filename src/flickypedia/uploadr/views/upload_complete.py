from flask import render_template
from flask_login import login_required

from flickypedia.types.uploads import UploadBatch, UploadBatchResults
from flickypedia.types.views import ViewResponse
from flickypedia.fs_queue import Task
from flickypedia.uploadr.uploads import uploads_queue


def get_completed_task(task_id: str) -> Task[UploadBatch, UploadBatchResults]:
    q = uploads_queue()
    task = q.read_task(task_id)

    assert task["state"] == "completed"
    assert all(
        item["state"] in {"succeeded", "failed"}
        for item in task["task_output"].values()
    )

    return task


@login_required
def upload_complete(task_id: str) -> ViewResponse:
    task = get_completed_task(task_id)

    successful_requests = []
    failed_requests = []
    upload_results = []

    for req in task["task_input"]["requests"]:
        photo_id = req["photo"]["id"]

        if task["task_output"][photo_id]["state"] == "succeeded":
            successful_requests.append(req)
            upload_results.append(task["task_output"][photo_id])
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
