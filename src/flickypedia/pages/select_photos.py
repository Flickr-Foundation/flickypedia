from flask import (
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import login_required
from flickr_url_parser import parse_flickr_url, NotAFlickrUrl, UnrecognisedUrl

from flickypedia.apis.flickr import FlickrApi, ResourceNotFound
from .find_photos import FlickrPhotoURLForm


def get_photos(parsed_url):
    api = FlickrApi(api_key=current_app.config["FLICKR_API_KEY"])

    if parsed_url["type"] == "single_photo":
        return [api.get_single_photo(photo_id=parsed_url["photo_id"])]
    else:
        raise TypeError


@login_required
def select_photos():
    try:
        flickr_url = request.args["flickr_url"]
        parsed_url = parse_flickr_url(flickr_url)
    except (KeyError, NotAFlickrUrl, UnrecognisedUrl):
        abort(400)

    api = FlickrApi(api_key=current_app.config["FLICKR_API_KEY"])

    try:
        try:
            photos = get_photos(parsed_url)
        except TypeError:
            flash(f"I don't know how to find photos at that URL yet!")
            session["flickr_url"] = flickr_url
            return redirect(url_for("find_photos"))

    except ResourceNotFound:
        label = {"single_photo": "photo"}[parsed_url["type"]]

        flash(f"There is no {label} at that URL!", category="flickr_url")
        session["flickr_url"] = flickr_url
        return redirect(url_for("find_photos"))

    form = FlickrPhotoURLForm()

    return render_template(
        "select_photos.html",
        flickr_url=flickr_url,
        parsed_url=parsed_url,
        form=form,
        photos=photos,
    )
