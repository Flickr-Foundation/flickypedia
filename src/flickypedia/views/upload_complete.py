from flask_login import login_required

from ._types import ViewResponse


@login_required
def upload_complete(task_id: str) -> ViewResponse:
    return 'wow you’re done!'
