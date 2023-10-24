from flask import (
    render_template,
)
from flask_login import login_required


@login_required
def prepare_info():
    return render_template("prepare_info.html", current_step="prepare_info")
