"""
A page where a user is shown a list of photos they've chosen,
and they have to add title/caption/other metadata

    - photo 1: title ____ / caption ____ / categories ____
    - photo 2: title ____ / caption ____ / categories ____
    - photo 3: title ____ / caption ____ / categories ____

This page gets two arguments as query parameters:

-   A comma-separated list of photo IDs in ``selected_photo_ids``
-   A pointer to a cached Flickr API response in ``cache_id``

"""

import datetime
from typing import cast, Any, Dict, List, TypedDict

from flask import abort, redirect, render_template, request, url_for
from flask_wtf import FlaskForm, Form
from flask_login import current_user, login_required
from flickr_photos_api import DateTaken, User as FlickrUser
from wtforms import FormField, HiddenField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
from wtforms.widgets import TextArea

from flickypedia.apis._types import Statement
from flickypedia.photos import (
    CategorisedPhotos,
    PhotoWithSdc,
    add_sdc_to_photos,
    categorise_photos,
)
from flickypedia.uploads import UploadRequest, begin_upload
from .select_photos import get_cached_photos_data, remove_cached_photos_data
from ._types import ViewResponse


class WikiFieldsForm(Form):
    # This is based on the restrictions from Wikimedia Commons.
    # Note that these are only loose limits -- the max length is actually
    # 240 bytes, nor characters.
    #
    # See https://commons.wikimedia.org/wiki/Commons:File_naming#Length
    title = StringField(validators=[DataRequired(), Length(min=5, max=240)])

    # Captions on Wikimedia Commons are limited to 250 characters
    # (which matches the behaviour of the Upload Wizard).
    #
    # The Upload Wizard enforces a minimum of 5 characters, which we mimic.
    #
    # See https://commons.wikimedia.org/w/index.php?title=Commons%3AFile_captions&oldformat=true#What_makes_a_good_caption
    short_caption = StringField(
        validators=[DataRequired(), Length(min=5, max=250)], widget=TextArea()
    )

    # The categories will be written in the textarea, one per line.
    #
    # See the comments in the form template.
    categories = StringField(widget=TextArea())

    original_format: str

    def validate_title(self, field: StringField) -> None:
        title = f"File:{field.data}.{self.original_format}"

        api = current_user.wikimedia_api()
        validation = api.validate_title(title=title)

        if validation["result"] != "ok":
            raise ValidationError(validation["text"])


def create_prepare_info_form(photos: List[PhotoWithSdc]) -> FlaskForm:
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
            cache_id = …
            submit = …
            photo_1 = FormField()
            photo_2 = FormField()
            photo_3 = FormField()

    The labels on each of the fields will be a dict with all the photo data,
    which can be used to render nice previews/labels.
    """

    class CustomForm(FlaskForm):
        cache_id = HiddenField("cache_id")
        upload = SubmitField("UPLOAD")

        # TODO: Get a proper list of languages here
        language = SelectField(
            "language", choices=[("en", "English"), ("de", "Deutsch")]
        )

    for p in photos:

        class FormForThisPhoto(WikiFieldsForm):
            # original_format is optional in the Flickr API, because
            # you might not get it if the owner has disabled downloads --
            # but it's always available for CC licensed photos.
            original_format = cast(str, p["photo"]["original_format"])

        setattr(
            CustomForm,
            f"photo_{p['photo']['id']}",
            FormField(FormForThisPhoto, label=p),  # type: ignore
        )

    return CustomForm()


class ShortCaption(TypedDict):
    language: str
    text: str


class PhotoForUpload(TypedDict):
    id: str
    title: str
    short_caption: ShortCaption
    categories: List[str]
    license_id: str
    date_taken: DateTaken
    date_posted: datetime.datetime
    original_url: str
    photo_url: str
    sdc: List[Statement]
    owner: FlickrUser


def create_upload_requests(
    photos: List[PhotoWithSdc], form_data: Dict[str, Any]
) -> List[UploadRequest]:
    upload_requests: List[UploadRequest] = []

    for photo_with_sdc in photos:
        photo = photo_with_sdc["photo"]
        this_photo_form_data = form_data[f"photo_{photo['id']}"]

        upload_requests.append(
            {
                "photo": photo,
                "sdc": photo_with_sdc["sdc"],
                "title": this_photo_form_data["title"] + "." + photo["original_format"],
                "caption": {
                    "language": form_data["language"],
                    "text": this_photo_form_data["short_caption"],
                },
                "categories": this_photo_form_data["categories"],
            }
        )

    return upload_requests


@login_required
def prepare_info() -> ViewResponse:
    try:
        selected_photo_ids = {
            photo_id
            for photo_id in request.args["selected_photo_ids"].split(",")
            if photo_id
        }
        cache_id = request.args["cache_id"]
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
    api_response = get_cached_photos_data(cache_id)

    selected_photos = [
        photo for photo in api_response["photos"] if photo["id"] in selected_photo_ids
    ]

    # Do some basic consistency checks.  These assertions could fail
    # if somebody has mucked around with the URL query parameters,
    #  but in that case I'm okay to let it fail.
    assert categorise_photos(selected_photos) == cast(
        CategorisedPhotos,
        {
            "available": selected_photos,
            "duplicates": {},
            "disallowed_licenses": {},
            "restricted": set(),
        },
    )

    # Next add the structured data to the photos.
    photos_with_sdc = add_sdc_to_photos(selected_photos)

    # Now construct the "prepare info" form.
    prepare_info_form = create_prepare_info_form(photos=photos_with_sdc)

    if prepare_info_form.validate_on_submit():

        upload_requests = create_upload_requests(
            photos_with_sdc, form_data=prepare_info_form.data
        )

        task_id = begin_upload(
            upload_requests=upload_requests,
        )

        return redirect(url_for("wait_for_upload", task_id=task_id))

    return render_template(
        "prepare_info/index.html",
        current_step="prepare_info",
        prepare_info_form=prepare_info_form,
        photo_fields=[
            field for field in prepare_info_form if field.id.startswith("photo_")
        ],
    )


def truncate_description(d: str) -> str:
    """
    Given a complete description from Flickr, truncate it so it's suitable
    for description on the "prepare info" screen.

    The rough target is "about 5–6 lines of text in the UI.
    """
    # Heuristic #1: because we preserve line breaks in the description,
    # make sure we don't display a silly number of lines.
    if len(d.splitlines()) > 5:
        return truncate_description("\n".join(d.splitlines()[:5])) + "…"

    # Heuristic #2: try to cut it about a target number of characters.
    #
    # The target length is a loose number, not a hard upper limit.
    target_length = 160

    # If we're already under the target length, we're already good.
    #
    # Allow a little bit of slop here.
    if len(d) <= target_length + 20:
        return d

    # Okay, so now truncate to the target length plus our slop.
    #
    # Then split on spaces and chop off the last word, so we don't
    # end mid-word.
    d = d[: target_length + 15]
    d, _ = d.rsplit(" ", 1)

    # How long is the last line?
    #
    # If it's short, trim the whole thing and go up to the previous line
    # rather than having a tiny line at the end.
    try:
        remainder, last_line = d.rsplit("\n", 1)
    except ValueError:  # no newlines
        pass
    else:
        if len(last_line) <= 10:
            d = remainder

    return d.strip() + "…"
