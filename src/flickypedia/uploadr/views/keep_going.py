from flask import render_template
from flask_login import login_required

from .get_photos import FlickrPhotoURLForm


@login_required
def keep_going() -> str:
    photo_url_form = FlickrPhotoURLForm()

    return render_template(
        "keep_going.html", photo_url_form=photo_url_form, flickr_url=""
    )
