from flask import abort, render_template, request
from flask_login import login_required
from flickr_url_parser import parse_flickr_url, NotAFlickrUrl, UnrecognisedUrl

from .find_photos import FlickrPhotoURLForm


@login_required
def prepare_info():
    try:
        flickr_url = request.args["flickr_url"]
        parsed_url = parse_flickr_url(flickr_url)
    except (KeyError, NotAFlickrUrl, UnrecognisedUrl):
        abort(400)

    form = FlickrPhotoURLForm()

    return render_template(
        "prepare_info.html", flickr_url=flickr_url, parsed_url=parsed_url, form=form
    )
