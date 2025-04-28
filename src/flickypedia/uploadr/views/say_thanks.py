from flask import render_template
from flask_login import login_required

from .upload_complete import get_completed_task


@login_required
def say_thanks(task_id: str) -> str:
    task = get_completed_task(task_id)

    return render_template("say_thanks.html", current_step="say_thanks", task=task)
