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
from flask_wtf import Form, FlaskForm
from wtforms import BooleanField, SelectMultipleField, SubmitField
from wtforms.validators import InputRequired
from wtforms import StringField, SubmitField, FieldList, FormField

from flickypedia.apis.flickr import FlickrApi, ResourceNotFound
from .find_photos import FlickrPhotoURLForm
from .select_photos import get_photos


def get_photos(parsed_url):
    """
    Given a correctly parsed URL, get a list of photos from the Flickr API.

    Note: this doesn't do any checking of the URLs for correct license,
    duplicates on Wikimedia Commons, etc.  It just returns a list of
    photos which can be found on Flickr.
    """
    api = FlickrApi(api_key=current_app.config["FLICKR_API_KEY"])

    if parsed_url["type"] == "single_photo":
        return {'photos':[api.get_single_photo(photo_id=parsed_url["photo_id"])]}
    elif parsed_url['type'] == 'album':
        return api.get_photos_in_album(
            user_url=parsed_url['user_url'],
            album_id=parsed_url['album_id']
        )
    else:
        raise TypeError


class SinglePhotoForm(Form):
    is_selected = BooleanField()


class SelectPhotosForm(FlaskForm):
    photos = FieldList(FormField(SinglePhotoForm))
    submit = SubmitField("Go")


@login_required
def prepare_info():
    flickr_url = request.args["flickr_url"]
    selected_photo_ids = set(request.args["selected_photo_ids"].split(","))

    parsed_url = parse_flickr_url(flickr_url)

    photo_data = get_photos(parsed_url)

    photo_data['photos'] = [
        p
        for p in photo_data['photos']
        if p['id'] in selected_photo_ids
    ]

    return render_template("prepare_info.html", flickr_url=flickr_url, selected_photo_ids=selected_photo_ids, photos=photo_data)