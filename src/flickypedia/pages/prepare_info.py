import collections

from flask import (
    abort,
    flash,
    render_template,
    request,
)
from flask_login import login_required
from flask_wtf import Form, FlaskForm
from wtforms import FieldList, FormField, HiddenField, SubmitField, StringField
from wtforms.validators import DataRequired

from flickypedia.pages.select_photos import get_cached_api_response


class PhotoInfoForm(Form):
    title = StringField()
    short_caption = StringField()
    categories = StringField()


class PrepareInfoForm(FlaskForm):
    """
    The form that has the list of photos for a user to enter metadata.
    """

    result_filename = HiddenField("result_filename")
    photos = FieldList(FormField(PhotoInfoForm))
    submit = SubmitField("Prepare info")


def create_prepare_info_form(photos):
    """
    Create a Flask form with a PhotoInfoForm (list of fields) for each
    photo in the list.  This allows us to render a form like:

        - photo 1: title ____ / caption ____ / categories ____
        - photo 2: title ____ / caption ____ / categories ____
        - photo 3: title ____ / caption ____ / categories ____

    even though the list of photos is created dynamically from
    the Flickr API.

    The created fields will have be boolean fields with the ID 'photo_{id}',
    similar to if we'd written:

        class PrepareInfoForm(FlaskForm):
            cached_api_response_id = …
            submit = …

            photo_1 = FormField()
            photo_2 = FormField()
            photo_3 = FormField()

    The labels on each of the fields will be a dict with all the photo data,
    which can be used to render nice previews/labels.

    """
    class PhotoInfoForm(Form):
        title = StringField(validators=[DataRequired()])
        short_caption = StringField(validators=[DataRequired()])
        categories = StringField()

    class CustomForm(FlaskForm):
        result_filename = HiddenField("result_filename")
        submit = SubmitField("Prepare info")

    for p in photos:
        setattr(CustomForm, f"photo_{p['id']}", FormField(PhotoInfoForm, label=p))

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
        ph for ph in photo_data["photos"] if ph["id"] in selected_photo_ids
    ]

    form = create_prepare_info_form(photos=selected_photos)

    # TODO: Check we have the right licenses here!

    if form.validate_on_submit():
        from pprint import pprint; pprint(form.data)

    return render_template(
        "prepare_info.html",
        selected_photo_ids=selected_photo_ids,
        cached_api_response_id=cached_api_response_id,
        photos=photo_data,
        form=form,
        current_step="prepare_info",
    )
