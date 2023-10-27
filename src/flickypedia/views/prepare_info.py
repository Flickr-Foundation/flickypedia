"""
A page where a user is shown a list of photos they've chosen,
and they have to add title/caption/other metadata

    - photo 1: title ____ / caption ____ / categories ____
    - photo 2: title ____ / caption ____ / categories ____
    - photo 3: title ____ / caption ____ / categories ____

This page gets two arguments as query parameters:

-   A comma-separated list of photo IDs in ``selected_photo_ids``
-   A pointer to a cached Flickr API response in ``cached_api_response_id``

"""

from flask import abort, current_app, flash, redirect, render_template, request, url_for
from flask_wtf import FlaskForm, Form
from flask_login import current_user, login_required
from wtforms import FormField, HiddenField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired

from flickypedia.apis.structured_data import create_sdc_claims_for_flickr_photo
from flickypedia.uploads import upload_batch_of_photos
from flickypedia.utils import size_at
from .select_photos import get_cached_api_response


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
        cached_api_response_id = HiddenField("cached_api_response_id")
        submit = SubmitField("Prepare info")

        # TODO: Get a proper list of languages here
        language = SelectField(
            "language", choices=[("en", "English"), ("de", "Deutsch")]
        )

    for p in photos:
        p["sdc"] = create_sdc_claims_for_flickr_photo(
            photo_id=p["id"],
            photo_url=p["url"],
            user=p["owner"],
            copyright_status="copyrighted",
            original_url=size_at(p["sizes"], desired_size="Original")["source"],
            license_id=p["license"]["id"],
            date_posted=p["date_posted"],
            date_taken=p["date_taken"],
        )
        setattr(CustomForm, f"photo_{p['id']}", FormField(PhotoInfoForm, label=p))

    return CustomForm()


def prepare_photos_for_upload(selected_photos, form_data):
    photos_to_upload = []

    for photo in selected_photos:
        this_photo_form_data = form_data[f"photo_{photo['id']}"]

        new_photo = {
            "id": photo["id"],
            "title": this_photo_form_data["title"],
            "short_caption": {
                "language": form_data["language"],
                "text": this_photo_form_data["short_caption"],
            },
            "categories": this_photo_form_data["categories"],
            "license_id": photo["license"]["id"],
            "date_taken": photo["date_taken"],
            "date_posted": photo["date_posted"],
            "original_url": size_at(photo["sizes"], desired_size="Original")["source"],
            "photo_url": photo["url"],
            "sdc": photo["sdc"],
            "owner": photo["owner"],
        }

        photos_to_upload.append(new_photo)

    return photos_to_upload


@login_required
def prepare_info():
    try:
        selected_photo_ids = {
            photo_id
            for photo_id in request.args["selected_photo_ids"].split(",")
            if photo_id
        }
        cached_api_response_id = request.args["cached_api_response_id"]
    except KeyError:
        abort(400)

    if not selected_photo_ids:
        abort(400)

    # Look up the cached Flickr API response from the previous stop.
    # We can then look up the list of photo from the list of selected
    # photo IDs.
    #
    # This will have the same order as the photos in the previous page,
    # so doing this filter will show the photos in the same order in
    # this page.
    api_response = get_cached_api_response(cached_api_response_id)

    selected_photos = [
        photo for photo in api_response["photos"] if photo["id"] in selected_photo_ids
    ]

    # Do some basic consistency checks.  These assertions could fail
    # if somebody has mucked around with the URL query parameters,
    #  but in that case I'm okay to let it fail.
    assert len(selected_photos) == len(selected_photo_ids)
    assert all(
        photo["license"]["id"] in current_app.config["ALLOWED_LICENSES"]
        for photo in selected_photos
    )

    # Now construct the "prepare info" form.
    prepare_info_form = create_prepare_info_form(photos=selected_photos)

    if prepare_info_form.validate_on_submit():
        photos_to_upload = prepare_photos_for_upload(
            selected_photos, form_data=prepare_info_form.data
        )

        upload_batch_of_photos.apply_async(
            kwargs={
                "oauth_info": {
                    "access_token": current_user.access_token(),
                    "access_token_expires": current_user.access_token_expires,
                    "refresh_token": current_user.refresh_token(),
                },
                "photos_to_upload": photos_to_upload,
            },
            task_id=cached_api_response_id,
        )

        # TODO: Clear out the cached API response

        flash("Ready to upload!")

        return redirect(
            url_for('wait_for_upload', task_id=cached_api_response_id)
        )

    return render_template(
        "prepare_info.html",
        current_step="prepare_info",
        prepare_info_form=prepare_info_form,
    )
