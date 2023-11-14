"""
A page where a user is shown a list of photos with checkboxes, and
they can choose which of them to upload to Wiki Commons.

    - [ ] photo 1
    - [ ] photo 2
    - [ ] photo 3

This page gets a single argument as input: a ``flickr_url`` query parameter
with the URL of the Flickr page provided by the user.

-   If we can find photos at that URL, we render them on the page for
    the user
-   If we can't find photos at that URL, we send the user back to the
    "enter a URL" page with an appropriate error message

To ensure a stable experience over reloads/further steps, we save the
initial API response from the Flickr API.  We can then retrieve this
later in the session.

TODO:

*   Limit the number of options you can submit

"""

import datetime
import json
import os
from typing import List
import uuid

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
from flask_login import current_user, login_required
from flickr_photos_api import (
    ResourceNotFound,
    SinglePhoto,
)
from flickr_url_parser import (
    parse_flickr_url,
    NotAFlickrUrl,
    UnrecognisedUrl,
)
from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, SubmitField
from wtforms.validators import DataRequired

from flickypedia.apis.flickr import get_photos_from_flickr, GetPhotosData
from flickypedia.utils import DatetimeDecoder, DatetimeEncoder
from flickypedia.photos import categorise_photos
from .get_photos import FlickrPhotoURLForm
from ._types import ViewResponse


class BaseSelectForm(FlaskForm):
    """
    Base for the "select photos" form.  This is split out from
    the "create" function below to make the view function more
    consistent -- see comments in that function.
    """

    cache_id = HiddenField("cache_id", validators=[DataRequired()])
    submit = SubmitField("PREPARE INFO")

    def selected_photo_ids(self) -> List[str]:
        raise NotImplementedError


def create_select_photos_form(photos: List[SinglePhoto]) -> BaseSelectForm:
    """
    Create a Flask form with a boolean field (checkbox) for each photo
    on the list.  This allows us to render a form like:

        - [ ] photo 1
        - [ ] photo 2
        - [ ] photo 3

    even though the list of photos is created dynamically from
    the Flickr API.

    The created fields will have be boolean fields with the ID 'photo_{id}',
    similar to if we'd written:

        class SelectPhotosForm(FlaskForm):
            cache_id = …
            submit = …

            photo_1 = BooleanField()
            photo_2 = BooleanField()
            photo_3 = BooleanField()

    The labels on each of the fields will be a dict with all the photo data,
    which can be used to render nice previews/labels.

    """

    class CustomForm(BaseSelectForm):
        def selected_photo_ids(self) -> List[str]:
            return [
                name.replace("photo_", "")
                for name, value in self.data.items()
                if name.startswith("photo_") and value
            ]

    for p in photos:
        setattr(CustomForm, f"photo_{p['id']}", BooleanField(label=p))  # type: ignore

    return CustomForm()


@login_required
def select_photos() -> ViewResponse:
    try:
        flickr_url = request.args["flickr_url"]
        parsed_url = parse_flickr_url(flickr_url)
    except (KeyError, NotAFlickrUrl, UnrecognisedUrl):
        abort(400)

    # If somebody's already visited the page and clicked the
    # "Prepare info" button, then we should have a cached API response
    # for them -- go ahead and retrieve it.
    #
    # At this point we can't construct the full form because we don't
    # have the list of IDs -- we'll do that shortly.
    #
    # TODO: What if we get an error looking up the cached API resp here?
    base_form = BaseSelectForm()

    if base_form.validate_on_submit():
        photo_data = get_cached_photos_data(
            response_id=base_form.cache_id.data  # type: ignore
        )

        cache_id = base_form.cache_id.data

    # If this is the first time somebody is visiting the page or
    # we don't have a cached API response, then load the photos
    # from the Flickr API.
    else:
        try:
            photo_data = get_photos_from_flickr(parsed_url)
            cache_id = save_cached_photos_data(photo_data)
        except ResourceNotFound:
            label = {"single_photo": "photo"}.get(
                parsed_url["type"], parsed_url["type"]
            )

            # If we aren't able to resolve this URL, send the user back to
            # the "find photos" page.  We put the URL they entered in the
            # session so we can prefill the form with it.
            flash(f"There is no {label} at that URL!", category="flickr_url")
            session["flickr_url"] = flickr_url
            return redirect(url_for("get_photos"))
        except TypeError:
            flash(
                "I don't know how to find photos at that URL yet!",
                category="flickr_url",
            )
            session["flickr_url"] = flickr_url
            return redirect(url_for("get_photos"))

    if parsed_url["type"] == "tag" and not photo_data["photos"]:
        flash("There are no photos with that tag!", category="flickr_url")
        session["flickr_url"] = flickr_url
        return redirect(url_for("get_photos"))

    # Categorise the photos, so we know if there are any duplicates
    # or photos with disallowed licenses.
    sorted_photos = categorise_photos(photo_data["photos"])

    # If we've got a single photo which is available, we can send the
    # user straight to the "prepare info" screen rather than making
    # them select a single item from the list.
    if parsed_url["type"] == "single_photo" and len(sorted_photos["available"]) == 1:
        return redirect(
            url_for(
                "prepare_info",
                selected_photo_ids=parsed_url["photo_id"],
                cache_id=cache_id,
            )
        )

    # TODO: If we know there are no photos available, then we can
    # delete the cached API response

    # At this point we know all the photos that should be in the list.
    # Go ahead and build the full form.
    select_photos_form = create_select_photos_form(photos=sorted_photos["available"])

    select_photos_form.cache_id.data = cache_id

    # Now check to see if somebody has submitted a form -- if so, we'll
    # take those IDs and send them to the next step.
    if select_photos_form.validate_on_submit():
        photo_ids = select_photos_form.selected_photo_ids()

        if photo_ids:
            # TODO: Are there going to be issues if we put lots of data
            # into this URL?  Maybe we should be POST-ing directly
            # to /prepare_info instead?
            return redirect(
                url_for(
                    "prepare_info",
                    selected_photo_ids=",".join(photo_ids),
                    cache_id=cache_id,
                )
            )
        else:
            flash("You need to select at least one photo!", category="select_photos")

    # Complete the route by rendering the template.
    return render_template(
        "select_photos/index.html",
        flickr_url=flickr_url,
        parsed_url=parsed_url,
        photo_url_form=FlickrPhotoURLForm(),
        select_photos_form=select_photos_form,
        photo_data={k: v for k, v in photo_data.items() if k != "photos"},
        current_step="get_photos",
        photos=sorted_photos,
    )


def get_cached_photos_data(response_id: str) -> GetPhotosData:
    """
    Retrieve some cached photos data.
    """
    cache_dir = current_app.config["FLICKR_API_RESPONSE_CACHE"]

    with open(os.path.join(cache_dir, response_id + ".json")) as infile:
        cached_data = json.load(infile, cls=DatetimeDecoder)

    return cached_data["value"]  # type: ignore


def save_cached_photos_data(response: GetPhotosData) -> str:
    """
    Save a cached API response.  Returns an ID which can be used to
    retrieve this response now.
    """
    cache_dir = current_app.config["FLICKR_API_RESPONSE_CACHE"]
    response_id = str(uuid.uuid4())

    os.makedirs(cache_dir, exist_ok=True)

    out_data = {
        "user": current_user.name,
        "now": datetime.datetime.now(),
        "value": response,
    }

    with open(os.path.join(cache_dir, response_id + ".json"), "w") as outfile:
        outfile.write(json.dumps(out_data, cls=DatetimeEncoder))

    return response_id


def remove_cached_photos_data(response_id: str) -> None:
    """
    Remove a cached API response.
    """
    cache_dir = current_app.config["FLICKR_API_RESPONSE_CACHE"]

    os.unlink(os.path.join(cache_dir, response_id + ".json"))
