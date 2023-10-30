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
from flickr_url_parser import parse_flickr_url, NotAFlickrUrl, UnrecognisedUrl
from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, SubmitField
from wtforms.validators import DataRequired

from flickypedia.apis.flickr import FlickrApi, ResourceNotFound, SafetyLevel
from flickypedia.duplicates import find_duplicates
from flickypedia.utils import DatetimeDecoder, DatetimeEncoder
from .get_photos import FlickrPhotoURLForm


def get_photos(parsed_url):
    """
    Given a correctly parsed URL, get a list of photos from the Flickr API.

    Note: this doesn't do any checking of the URLs for correct license,
    duplicates on Wikimedia Commons, etc.  It just returns a list of
    photos which can be found on Flickr.
    """
    api = FlickrApi(
        api_key=current_app.config["FLICKR_API_KEY"],
        user_agent=current_app.config["USER_AGENT"],
    )

    if parsed_url["type"] == "single_photo":
        return {"photos": [api.get_single_photo(photo_id=parsed_url["photo_id"])]}
    elif parsed_url["type"] == "album":
        return api.get_photos_in_album(
            user_url=parsed_url["user_url"],
            album_id=parsed_url["album_id"],
            per_page=current_app.config["PHOTOS_PER_PAGE"],
        )
    else:
        raise TypeError


def categorise_photos(all_photos):
    """
    Given a list of photos from the Flickr API, split them into
    three lists:

    -   okay to choose ("available")
    -   already on Wikimedia Commons ("duplicates")
    -   using a license not allowed on WMC ("disallowed_license")
    -   with a safety level not allowed on WMC ("restricted")

    """
    duplicates = find_duplicates(flickr_photo_ids=[photo["id"] for photo in all_photos])

    disallowed_licenses = {
        photo["id"]: photo["license"]["label"]
        for photo in all_photos
        # Note: it's possible that a photo with a disallowed license
        # may already be on Wikimedia Commons.
        #
        # We want to avoid putting it in this list so we don't
        # double-count photos.
        if photo["license"]["id"] not in current_app.config["ALLOWED_LICENSES"]
        and photo["id"] not in duplicates
    }

    restricted_photos = {
        photo["id"]
        for photo in all_photos
        if photo["id"] not in duplicates
        and photo["id"] not in disallowed_licenses
        and photo["safety_level"] != SafetyLevel.Safe
    }

    available_photos = [
        photo
        for photo in all_photos
        if photo["id"] not in duplicates
        and photo["id"] not in disallowed_licenses
        and photo["id"] not in restricted_photos
    ]

    assert len(duplicates) + len(disallowed_licenses) + len(available_photos) + len(
        restricted_photos
    ) == len(all_photos)

    return {
        "duplicates": duplicates,
        "disallowed_licenses": disallowed_licenses,
        "restricted": restricted_photos,
        "available": available_photos,
    }


class BaseSelectForm(FlaskForm):
    """
    Base for the "select photos" form.  This is split out from
    the "create" function below to make the view function more
    consistent -- see comments in that function.
    """

    cached_api_response_id = HiddenField(
        "cached_api_response_id", validators=[DataRequired()]
    )
    submit = SubmitField("PREPARE INFO")


def create_select_photos_form(photos):
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
            cached_api_response_id = …
            submit = …

            photo_1 = BooleanField()
            photo_2 = BooleanField()
            photo_3 = BooleanField()

    The labels on each of the fields will be a dict with all the photo data,
    which can be used to render nice previews/labels.

    """

    class CustomForm(BaseSelectForm):
        def selected_photo_ids(self):
            return [
                name.replace("photo_", "")
                for name, value in self.data.items()
                if name.startswith("photo_") and value
            ]

    for p in photos:
        setattr(CustomForm, f"photo_{p['id']}", BooleanField(label=p))

    return CustomForm()


@login_required
def select_photos():
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
        photo_data = get_cached_api_response(
            response_id=base_form.cached_api_response_id.data
        )

        cached_api_response_id = base_form.cached_api_response_id.data

    # If this is the first time somebody is visiting the page or
    # we don't have a cached API response, then load the photos
    # from the Flickr API.
    else:
        try:
            photo_data = get_photos(parsed_url)
            cached_api_response_id = save_cached_api_response(photo_data)
        except ResourceNotFound:
            label = {"single_photo": "photo", "album": "album"}[parsed_url["type"]]

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

    # Categorise the photos, so we know if there are any duplicates
    # or photos with disallowed licenses.
    photo_data["photos"] = categorise_photos(photo_data["photos"])

    # If we've got a single photo which is available, we can send the
    # user straight to the "prepare info" screen rather than making
    # them select a single item from the list.
    if (
        parsed_url["type"] == "single_photo"
        and len(photo_data["photos"]["available"]) == 1
    ):
        return redirect(
            url_for(
                "prepare_info",
                selected_photo_ids=parsed_url["photo_id"],
                cached_api_response_id=cached_api_response_id,
            )
        )

    # TODO: If we know there are no photos available, then we can
    # delete the cached API response

    # At this point we know all the photos that should be in the list.
    # Go ahead and build the full form.
    select_photos_form = create_select_photos_form(
        photos=photo_data["photos"]["available"]
    )

    select_photos_form.cached_api_response_id.data = cached_api_response_id

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
                    cached_api_response_id=cached_api_response_id,
                )
            )
        else:
            flash("You need to select at least one photo!", category="select_photos")

    # Complete the route by rendering the template.
    return render_template(
        "select_photos.html",
        flickr_url=flickr_url,
        parsed_url=parsed_url,
        photo_url_form=FlickrPhotoURLForm(),
        select_photos_form=select_photos_form,
        photo_data=photo_data,
        current_step="get_photos",
        photos=photo_data["photos"],
    )


def get_cached_api_response(response_id):
    """
    Retrieved a cached API response.
    """
    cache_dir = current_app.config["FLICKR_API_RESPONSE_CACHE"]

    with open(os.path.join(cache_dir, response_id + ".json")) as infile:
        cached_data = json.load(infile, cls=DatetimeDecoder)

    return cached_data["value"]


def save_cached_api_response(response):
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


def remove_cached_api_response(response_id):
    """
    Remove a cached API response.
    """
    cache_dir = current_app.config["FLICKR_API_RESPONSE_CACHE"]

    os.unlink(os.path.join(cache_dir, response_id + ".json"))
