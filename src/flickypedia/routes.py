from flask import redirect, render_template, jsonify, url_for
from flask_login import login_required

from flickypedia import app
from flickypedia.auth import (
    logout,
    oauth2_authorize_wikimedia,
    oauth2_callback_wikimedia,
)
from flickypedia.tasks import get_status, upload_images
from flickypedia.uploads import UploadPhotoForm, upload_batch_of_photos


app.add_url_rule("/logout", view_func=logout)
app.add_url_rule("/authorize/wikimedia", view_func=oauth2_authorize_wikimedia)
app.add_url_rule("/callback/wikimedia", view_func=oauth2_callback_wikimedia)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/go")
def go():
    result = upload_images.delay(10)
    return f"Go! <a href='/result/{result.id}'>{result.id}</a>"


@app.route("/result/<task_id>")
def task_result(task_id: str):
    return jsonify(get_status(task_id=task_id))


@app.route("/upload_photos", methods=["GET", "POST"])
@login_required
def upload_photos():
    form = UploadPhotoForm()

    if form.validate_on_submit and form.photo_id.data:
        photos = [
            {'id': f'{form.photo_id.data}-{i}'}
            for i in range(10)
        ]

        task_id = upload_batch_of_photos.delay(
            oauth_info=None,
            photos=photos
        )

        return redirect(url_for("progress", task_id=task_id))

    return render_template("upload_photos.html", form=form)


@app.route("/progress/<task_id>")
@login_required
def progress(task_id):
    return render_template("progress.html", task_id=task_id)
