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


@login_required
def prepare_info():
    try:
        selected_photo_ids = set(request.args["selected_photo_ids"].split(","))
        cached_api_response_id = request.args["cached_api_response_id"]
    except KeyError:
        abort(400)

    photo_data = get_cached_api_response(cached_api_response_id)

    photo_data["photos"] = [
        ph for ph in photo_data["photos"] if ph["id"] in selected_photo_ids
    ]

    # TODO: Check we have the right licenses here!

    form = PrepareInfoForm(photos=photo_data["photos"])

    if form.validate_on_submit():
        has_errors = False

        data = collections.defaultdict(dict)

        for photo_id in selected_photo_ids:
            if not request.form[f"photo-{photo_id}-title"]:
                flash("required", category=f"photo-{photo_id}-title")
                has_errors = True
            else:
                data[photo_id]["title"] = request.form[f"photo-{photo_id}-title"]

            if not request.form[f"photo-{photo_id}-caption"]:
                flash("required", category=f"photo-{photo_id}-caption")
                has_errors = True
            else:
                data[photo_id]["caption"] = request.form[f"photo-{photo_id}-caption"]

            data[photo_id]["categories"] = request.form[f"photo-{photo_id}-categories"]

        from pprint import pprint

        pprint(data)
    else:
        data = collections.defaultdict(dict)

    # from pprint import pprint; pprint(photo_data)

    return render_template(
        "prepare_info.html",
        selected_photo_ids=selected_photo_ids,
        cached_api_response_id=cached_api_response_id,
        photos=photo_data,
        form=form,
        data=data,
        current_step="prepare_info",
    )
