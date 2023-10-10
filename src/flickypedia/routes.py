from flask import render_template
from flask_login import current_user, login_required

from flickypedia import app
from flickypedia.apis.wikimedia import WikimediaApi
from flickypedia.forms import UploadPhotoForm


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload_photos", methods=["GET", "POST"])
@login_required
def upload_photos():
    form = UploadPhotoForm()

    if form.validate_on_submit:
        api = WikimediaApi(access_token=current_user.access_token())

        api.upload_photo(
            photo_url=form.photo_url.data,
            filename=form.filename.data,
            license=form.license.data,
            short_caption=form.short_caption.data,
        )

        print(api)

    return render_template("upload_photos.html", form=form)
