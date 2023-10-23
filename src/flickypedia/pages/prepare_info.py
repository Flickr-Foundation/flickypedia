import collections
import json
import os

from flask import (
abort,
current_app,
flash,
    render_template,
    request,
)
from flask_login import login_required
from flask_wtf import Form, FlaskForm
from wtforms import FieldList, FormField, HiddenField, SubmitField, StringField


class PhotoInfoForm(Form):

    title = StringField()
    short_caption = StringField()
    categories = StringField()


class PrepareInfoForm(FlaskForm):
    """
    The form that has the list of photos for a user to enter metadata.

    Because the list of photos changes per-request, we don't include
    it in this form -- instead, we render it in the HTML on the page.
    This from exists primarily for CSRF protection.
    """

    result_filename = HiddenField("result_filename")
    photos = FieldList(FormField(PhotoInfoForm))
    submit = SubmitField("Prepare info")


@login_required
def prepare_info():
    try:
        selected_photo_ids = set(request.args["selected_photo_ids"].split(","))
        result_filename = request.args["result_filename"]
    except (KeyError, NotAFlickrUrl, UnrecognisedUrl):
        abort(400)

    cached_results_path = os.path.join(
        current_app.config["FLICKR_API_RESPONSE_CACHE"], result_filename
    )


    try:
        photo_data = json.load(open(cached_results_path))
    except FileNotFoundError:
        raise


    photo_data['photos'] = [
        ph
        for ph in photo_data['photos']
        if ph['id'] in selected_photo_ids
    ]


    from pprint import pprint; pprint(selected_photo_ids)

    form = PrepareInfoForm(
        photos=photo_data['photos']
    )

    # for photo in photo_data['photos']:


    if form.validate_on_submit():
        has_errors = False

        data = collections.defaultdict(dict)

        for photo_id in selected_photo_ids:
            if not request.form[f'photo-{photo_id}-title']:
                flash('required', category=f'photo-{photo_id}-title')
                has_errors = True
            else:
                data[photo_id]['title'] = request.form[f'photo-{photo_id}-title']

            if not request.form[f'photo-{photo_id}-caption']:
                flash('required', category=f'photo-{photo_id}-caption')
                has_errors = True
            else:
                data[photo_id]['caption'] = request.form[f'photo-{photo_id}-caption']

            data[photo_id]['categories'] = request.form[f'photo-{photo_id}-categories']

        from pprint import pprint; pprint(data)


    # from pprint import pprint; pprint(photo_data)




    return render_template("prepare_info.html", selected_photo_ids=selected_photo_ids, result_filename=result_filename, photos=photo_data, form=form, data=data)
