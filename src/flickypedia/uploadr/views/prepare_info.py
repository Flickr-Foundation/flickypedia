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
import json
import typing

from flask import abort, redirect, render_template, request, url_for
from flask_wtf import FlaskForm, Form
from flask_login import current_user, login_required
from flickr_photos_api import DateTaken, User as FlickrUser
from nitrate.types import validate_type
from wtforms import (
    BooleanField,
    FormField,
    HiddenField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired, Length, ValidationError
from wtforms.widgets import TextArea

from flickypedia.apis.wikimedia import top_n_languages, LanguageMatch
from flickypedia.photos import (
    CategorisedPhotos,
    EnrichedPhoto,
    enrich_photo,
    categorise_photos,
)
from flickypedia.types.structured_data import NewClaims
from flickypedia.types.views import ViewResponse
from flickypedia.types.uploads import UploadRequest
from ..uploads import begin_upload
from ..caching import get_cached_photos_data, remove_cached_photos_data


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


class PrepareInfoFormBase(FlaskForm):
    cache_id = HiddenField("cache_id")
    upload = SubmitField("UPLOAD")

    # For language selection we have two user interfaces:
    #
    #     * For no-JS users, we have a <select> field with a dropdown of
    #       the ten most commonly-used languages on Commons.
    #     * For JS users, we have an <input type="text"> field where they
    #       can search for languages.
    #
    # These are two separate fields.
    #
    # We need to know which of the two fields to look at, so we include
    # a hidden checkbox which gets ticked by the JavaScript that sets up
    # language search on the JS-enabled field.
    js_enabled = BooleanField("js_enabled")
    no_js_language = SelectField(
        "no_js_language", choices=[("", "")] + top_n_languages(n=10)
    )
    js_language = StringField("js_language")

    def get_js_language(self) -> LanguageMatch | None:
        try:
            if isinstance(self.js_language.data, str):
                data = json.loads(self.js_language.data)
                return validate_type(data, model=LanguageMatch)
        except Exception:
            pass

        return None

    def validate_no_js_language(self, field: SelectField) -> None:
        if self.get_js_language() is None and self.no_js_language.data == "":
            raise ValidationError

    @property
    def language(self) -> str:
        if self.js_enabled.data:
            language = self.get_js_language()
            if language is None:  # pragma: no cover
                raise ValidationError
            return language["id"]
        else:
            assert isinstance(self.no_js_language.data, str)
            return self.no_js_language.data


def create_prepare_info_form(photos: list[EnrichedPhoto]) -> PrepareInfoFormBase:
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

    class CustomForm(PrepareInfoFormBase):
        pass

    for p in photos:

        class FormForThisPhoto(WikiFieldsForm):
            # original_format is optional in the Flickr API, because
            # you might not get it if the owner has disabled downloads --
            # but it's always available for CC licensed photos.
            original_format = typing.cast(str, p["photo"]["original_format"])

        setattr(
            CustomForm,
            f"photo_{p['photo']['id']}",
            FormField(FormForThisPhoto, label=p),  # type: ignore
        )

    return CustomForm()


class ShortCaption(typing.TypedDict):
    language: str
    text: str


class PhotoForUpload(typing.TypedDict):
    id: str
    title: str
    short_caption: ShortCaption
    categories: list[str]
    license_id: str
    date_taken: DateTaken
    date_posted: datetime.datetime
    original_url: str
    photo_url: str
    sdc: NewClaims
    owner: FlickrUser


def create_upload_requests(
    photos: list[EnrichedPhoto], form_data: dict[str, typing.Any], language: str
) -> list[UploadRequest]:
    upload_requests: list[UploadRequest] = []

    for enriched_photo in photos:
        photo = enriched_photo["photo"]
        this_photo_form_data = form_data[f"photo_{photo['id']}"]

        categories = this_photo_form_data["categories"].strip().splitlines()

        upload_requests.append(
            {
                "photo": photo,
                "sdc": enriched_photo["sdc"],
                "title": this_photo_form_data["title"] + "." + photo["original_format"],
                "caption": {
                    "language": language,
                    "text": this_photo_form_data["short_caption"],
                },
                "categories": categories,
                "username": current_user.name,
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
    assert categorise_photos(selected_photos) == typing.cast(
        CategorisedPhotos,
        {
            "available": selected_photos,
            "duplicates": {},
            "disallowed_licenses": {},
            "restricted": set(),
        },
    )

    # Next add the structured data to the photos.
    enriched_photos = enrich_photo(
        selected_photos,
        wikimedia_username=current_user.name,
        retrieved_at=api_response["retrieved_at"],
    )

    # Now construct the "prepare info" form.
    prepare_info_form = create_prepare_info_form(photos=enriched_photos)

    if prepare_info_form.validate_on_submit():
        language = prepare_info_form.language

        upload_requests = create_upload_requests(
            enriched_photos, form_data=prepare_info_form.data, language=language
        )

        task_id = begin_upload(upload_requests=upload_requests)

        remove_cached_photos_data(cache_id)

        return redirect(url_for("wait_for_upload", task_id=task_id))

    return render_template(
        "prepare_info/index.html",
        current_step="prepare_info",
        prepare_info_form=prepare_info_form,
        photo_fields=[
            field for field in prepare_info_form if field.id.startswith("photo_")
        ],
        api_urls={
            "validate_title": url_for("validate_title_api"),
            "find_matching_categories": url_for("find_matching_categories_api"),
            "find_matching_languages": url_for("find_matching_languages_api"),
        },
    )


class TruncationResult(typing.TypedDict):
    text: str
    truncated: bool


def truncate_description(d: str) -> TruncationResult:
    """
    Given a complete description from Flickr, truncate it so it's suitable
    for description on the "prepare info" screen.

    The rough target is "about 5–6 lines of text in the UI.
    """
    # Heuristic #1: because we preserve line breaks in the description,
    # make sure we don't display a silly number of lines.
    if len(d.splitlines()) > 4:
        return {
            "text": truncate_description("\n".join(d.splitlines()[:4]))["text"],
            "truncated": True,
        }

    # Heuristic #2: try to cut it about a target number of characters.
    #
    # The target length is a loose number, not a hard upper limit.
    target_length = 140

    # If we're already under the target length, we're already good.
    #
    # Allow a little bit of slop here.
    if len(d) <= target_length + 20:
        return {"text": d, "truncated": False}

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

    return {"text": d.strip(), "truncated": True}
