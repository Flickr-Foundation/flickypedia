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
from flask_login import login_required
from flickr_url_parser import parse_flickr_url, NotAFlickrUrl, UnrecognisedUrl
from flask_wtf import FlaskForm
from wtforms import HiddenField, SubmitField

from flickypedia.apis.flickr import FlickrApi, ResourceNotFound
from flickypedia.utils import DatetimeEncoder
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
        return {"photos": [api.get_single_photo(photo_id=parsed_url["photo_id"])]}
    elif parsed_url["type"] == "album":
        return api.get_photos_in_album(
            user_url=parsed_url["user_url"], album_id=parsed_url["album_id"]
        )
    else:
        raise TypeError


class SelectPhotosForm(FlaskForm):
    """
    The form that has the list of photos for a user to select from,
    i.e. a list of photos with checkboxes.

    Because the list of photos changes per-request, we don't include
    it in this form -- instead, we render it in the HTML on the page.
    This from exists primarily for CSRF protection.
    """

    result_filename = HiddenField("result_filename")
    submit = SubmitField("Prepare info")


@login_required
def select_photos():
    try:
        flickr_url = request.args["flickr_url"]
        parsed_url = parse_flickr_url(flickr_url)
    except (KeyError, NotAFlickrUrl, UnrecognisedUrl):
        abort(400)

    # Create the "select photos" form -- if it's present and has a
    # non-empty selection of photos, then we can skip straight to
    # the next step without looking up anything in the Flickr API.
    select_photos_form = SelectPhotosForm()

    if select_photos_form.validate_on_submit():
        # The form data is an immutable dict of the form
        #
        #     [('result_filename', 'dbd1557d-3239-436d-949f-05f270f2f7ad.json'),
        #      ('csrf_token', 'IjFhZ…'),
        #      ('photo_5536044022', 'on'),
        #      ('photo_5536043704', 'on'),
        #      ('submit', 'Prepare info')
        #     ]
        #
        # We have to use the raw form data because the photos aren't on
        # the FlaskForm -- see comment on SelectPhotosForm.
        selected_photo_ids = [
            name.replace("photo_", "")
            for name, value in request.form.items()
            if name.startswith("photo_") and value == "on"
        ]

        # If the user hasn't selected any photos, tell them to try again!
        if not selected_photo_ids:
            flash("You need to select at least one photo!", category="select_photos")
        else:
            # TODO: Are there going to be issues if we put lots of data
            # into this endpoint?  Maybe we should be POST-ing directly
            # to /prepare_info instead?
            return redirect(
                url_for(
                    "prepare_info",
                    flickr_url=flickr_url,
                    selected_photo_ids=",".join(selected_photo_ids),
                    result_filename=select_photos_form.result_filename.data,
                )
            )

    # If the user hasn't chosen some photos, instead go off to the
    # Flickr API and load them.  We'll then use these to render a list
    # of checkboxes on the page.
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

    # If we've got some results from Flickr, save them to a local file
    # on disk and add the name to the form.
    #
    # This means we can pass the same set of results to subsequent steps
    # without worrying about results changing in the API (e.g. if somebody
    # looks at an album and new photos are added halfway through).
    out_filename = f"{uuid.uuid4()}.json"

    out_path = os.path.join(
        current_app.config["FLICKR_API_RESPONSE_CACHE"], out_filename
    )

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(out_path, "w") as out_file:
        out_file.write(json.dumps(photo_data, cls=DatetimeEncoder))

    select_photos_form.result_filename.data = out_filename

    # Complete the route by rendering the template.
    return render_template(
        "select_photos.html",
        flickr_url=flickr_url,
        parsed_url=parsed_url,
        photo_url_form=FlickrPhotoURLForm(),
        select_photos_form=select_photos_form,
        photo_data=photo_data,
    )
