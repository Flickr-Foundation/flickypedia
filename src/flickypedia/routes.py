from flask import render_template
from flask_login import current_user, login_required

from flickypedia import app
from flickypedia.apis.wikimedia import WikimediaApi
from flickypedia.apis.structured_data import create_sdc_claims_for_flickr_photo
from flickypedia.forms import UploadPhotoForm


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload_photos", methods=["GET", "POST"])
@login_required
def upload_photos():
    form = UploadPhotoForm()

    print(current_user.access_token())

    if form.validate_on_submit and form.photo_id.data:
        api = WikimediaApi(access_token=current_user.access_token())

        print(form.date_taken.data)
        print(form.posted_date.data)

        structured_data = create_sdc_claims_for_flickr_photo(
            photo_id=form.photo_id.data,
            user_id=form.user_id.data,
            username=form.username.data,
            realname=form.realname.data,
            copyright_status="copyrighted",
            jpeg_url=form.jpeg_url.data,
            license_id=form.license_id.data,
            posted_date=form.posted_date.data,
            date_taken=form.date_taken.data,
            taken_unknown=form.taken_unknown.data,
            taken_granularity=form.taken_granularity.data,
        )

        api.upload_photo(
            jpeg_url=form.jpeg_url.data,
            filename=form.filename.data,
            license=form.license_id.data,
            short_caption=form.short_caption.data,
            structured_data=structured_data,
        )

        print(api)

    return render_template("upload_photos.html", form=form)
