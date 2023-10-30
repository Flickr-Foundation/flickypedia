from flask import (
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import login_required
from flask_wtf import FlaskForm
from flickr_url_parser import parse_flickr_url, NotAFlickrUrl, UnrecognisedUrl
from wtforms import URLField, SubmitField
from wtforms.validators import DataRequired

from flickypedia.tasks import get_status


@login_required
def wait_for_upload(task_id):
    return render_template(
        "wait_for_upload.html", task_id=task_id, current_step="upload_to_wikimedia"
    )


@login_required
def get_upload_status(task_id):
    status = get_status(task_id)

    return jsonify(status)
