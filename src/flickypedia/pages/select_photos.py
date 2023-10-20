from flask import abort, current_app, render_template, request
from flask_login import login_required
from flickr_url_parser import parse_flickr_url, NotAFlickrUrl, UnrecognisedUrl

from flickypedia.apis.flickr import FlickrApi
from .find_photos import FlickrPhotoURLForm


# def get_single_photo(flickr_url, photo_id, api):



@login_required
def select_photos():
    try:
        flickr_url = request.args["flickr_url"]
        parsed_url = parse_flickr_url(flickr_url)
    except (KeyError, NotAFlickrUrl, UnrecognisedUrl):
        abort(400)

    api = FlickrApi(api_key=current_app.config['FLICKR_API_KEY'])

    form = FlickrPhotoURLForm()

    return render_template(
        "select_photos.html", flickr_url=flickr_url, parsed_url=parsed_url, form=form
    )
