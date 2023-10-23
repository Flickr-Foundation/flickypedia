"""
A page where a user is shown a list of all the photos they've chosen,
and they have to fill in a title/short caption for use on Commons.

    - image 1

      title:          _____
      short caption:  _____
      categories:     _____

    - image 2

      title:          _____
      short caption:  _____
      categories:     _____

This page gets two arguments as input:

1.  A comma-separated list of Flickr photo IDs in the `selected_photo_ids`
    query parameter
2.  The ID of a cached Flickr API response in the `cached_api_response_id`
    query parameter

TODO:

*   Add limits to the length of the short caption field

"""

from flask import (
flash,
    render_template,
    request,
)
from flask_login import login_required
from flask_wtf import FlaskForm, Form
from wtforms import FormField, HiddenField, StringField, SubmitField
from wtforms.validators import DataRequired

from flickypedia.pages.select_photos import get_cached_api_response


class PerPhotoForm(Form):
    title = StringField(validators=[DataRequired()])
    short_caption = StringField(validators=[DataRequired()])
    categories = StringField()


def create_prepare_info_form(photos):
    """
    Create a Flask form with a per-photo form for each photo.
    """
    class CustomForm(FlaskForm):
        cached_api_response_id = HiddenField(
            "cached_api_response_id", validators=[DataRequired()]
        )
        submit = SubmitField("Prepare info")

    for p in photos:
        setattr(CustomForm, f"photo_{p['id']}", FormField(
            PerPhotoForm,
            label=p
        ))

    return CustomForm()


@login_required
def prepare_info():
    try:
        selected_photo_ids = set(request.args["selected_photo_ids"].split(","))
        cached_api_response_id = request.args["cached_api_response_id"]
    except KeyError:
        abort(400)

    photo_data = get_cached_api_response(cached_api_response_id)

    selected_photos = [
        photo
        for photo in photo_data['photos']
        if photo['id'] in selected_photo_ids
    ]

    form = create_prepare_info_form(selected_photos)
    form.cached_api_response_id.data = cached_api_response_id

    if form.validate_on_submit():
        flash("You’re ready to upload to Wikimedia Commons!")
        from pprint import pprint; pprint(form.data)

    return render_template("prepare_info.html", selected_photos=selected_photos, form=form)
