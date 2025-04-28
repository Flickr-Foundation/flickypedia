from flask import flash, redirect, render_template, request, session, url_for
from flask_login import login_required
from flask_wtf import FlaskForm
from flickr_url_parser import parse_flickr_url, NotAFlickrUrl, UnrecognisedUrl
import werkzeug
from wtforms import URLField, SubmitField
from wtforms.validators import DataRequired


@login_required
def get_photos() -> str | werkzeug.Response:
    photo_url_form = FlickrPhotoURLForm()

    if photo_url_form.validate_on_submit():
        url = photo_url_form.flickr_url.data
        assert url is not None

        # Try to parse this as a Flickr URL.  If parsing fails for
        # some reason, return the user to the page.
        #
        # Make sure the input field still contains the URL they typed in,
        # so they can adjust what they typed previously.
        try:
            parse_flickr_url(url)
        except NotAFlickrUrl:
            flash("That URL doesn’t live on Flickr.com", category="flickr_url")
            return render_template(
                "get_photos.html",
                photo_url_form=photo_url_form,
                current_step="get_photos",
                flickr_url=url,
            )
        except UnrecognisedUrl:
            flash("There are no photos to show at that URL", category="flickr_url")
            return render_template(
                "get_photos.html",
                photo_url_form=photo_url_form,
                current_step="get_photos",
                flickr_url=url,
            )

        return redirect(url_for("select_photos", flickr_url=url))

    # We may end up on this page for several reasons, e.g.:
    #
    #   -   if something went wrong at the "select photos" step,
    #       say the URL look valid but actually returns a 404.
    #
    #   -   if the user tries to submit the form, but the CSRF token
    #       has expired.
    #
    # In that case, we want to prefill the form with the URL the user
    # entered previously, if they want to edit it and try again.
    #
    # We don't want to _submit_ their form, but we do want to preserve
    # their previous input.
    #
    if "flickr_url" in session:
        flickr_url = session.pop("flickr_url", "")
    elif "flickr_url" in request.form:
        flickr_url = request.form["flickr_url"]
    else:
        flickr_url = ""

    return render_template(
        "get_photos.html",
        photo_url_form=photo_url_form,
        flickr_url=flickr_url,
        current_step="get_photos",
    )


class FlickrPhotoURLForm(FlaskForm):
    """
    A form with a single input field where the user can enter a Flickr URL.
    """

    flickr_url = URLField(validators=[DataRequired()])

    submit = SubmitField("GO")
