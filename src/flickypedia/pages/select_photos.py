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


# def create_form(list_of_photos):
#     class SelectPhotosForm(FlaskForm):
#         submit = SubmitField("Go")
#         photos = []
#
#     for photo in list_of_photos:
#         setattr(
#             SelectPhotosForm, f"photo_{photo['id']}",
#             BooleanField(photo['id'])
#         )
#         SelectPhotosForm.photos.append(
#             getattr(SelectPhotosForm, f"photo_{photo['id']}")
#         )
#
#     return SelectPhotosForm()


@login_required
def select_photos():
    try:
        flickr_url = request.args["flickr_url"]
        parsed_url = parse_flickr_url(flickr_url)
    except KeyError:
        return redirect(url_for('find_photos'))
    except (KeyError, NotAFlickrUrl, UnrecognisedUrl):
        abort(400)

    try:
        photo_data = get_photos(parsed_url)
    except TypeError:
        flash(
            "I don't know how to find photos at that URL yet!",
            category="flickr_url",
        )
        session["flickr_url"] = flickr_url
        return redirect(url_for("find_photos"))

    except ResourceNotFound:
        label = {"single_photo": "photo"}[parsed_url["type"]]

        # If we aren't able to resolve this URL, send the user back to
        # the "find photos" page.  We put the URL they entered in the
        # session so we can prefill the form with it.
        flash(f"There is no {label} at that URL!", category="flickr_url")
        session["flickr_url"] = flickr_url
        return redirect(url_for("find_photos"))

    form = FlickrPhotoURLForm()

    select_form = SelectPhotosForm()

    if select_form.validate_on_submit():
        # ImmutableMultiDict([('csrf_token', 'ImE4ZWYxMTk4NTUzN2EwYWZiZTUxOGIxOTFlZjQzYWUxMzI2NzE1OTgi.ZTKQsw._OMuJsMGEfTMkAYV5TU-SvCM6hw'), ('photo-5536044022', 'on'), ('photo-5535465571', 'on'), ('photo-5535465269', 'on'), ('submit', 'Go')])
        selected_photo_ids = [
            name.replace('photo-', '')
            for name, value in request.form.items()
            if name.startswith('photo-') and value == 'on'
        ]

        known_photo_ids = {photo['id'] for photo in photo_data['photos']}

        if not set(selected_photo_ids).issubset(known_photo_ids):
            abort(400)

        # Check these IDs are in the original list maybe?

        return redirect(
            url_for(
                'prepare_info',
                flickr_url=flickr_url,
                selected_photo_ids=",".join(selected_photo_ids)
            )
        )

    return render_template(
        "select_photos.html",
        flickr_url=flickr_url,
        parsed_url=parsed_url,
        form=form,
        select_form=select_form,
        photo_data=photo_data,
    )
