from flask import flash, redirect, render_template, session, url_for
from flask_login import login_required
from flask_wtf import FlaskForm
from flickr_url_parser import parse_flickr_url, NotAFlickrUrl, UnrecognisedUrl
from wtforms import URLField, SubmitField
from wtforms.validators import DataRequired


@login_required
def find_photos():
    form = FlickrPhotoURLForm()

    if form.validate_on_submit():
        url = form.flickr_url.data

        # Try to parse this as a Flickr URL.  If parsing fails for
        # some reason, return the user to the page.
        #
        # Make sure the input field still contains the URL they typed in,
        # so they can adjust what they typed previously.
        try:
            parse_flickr_url(url)
        except NotAFlickrUrl:
            flash("That URL doesn’t live on Flickr.com", category="flickr_url")
            return render_template("find_photos.html", form=form, flickr_url=url)
        except UnrecognisedUrl:
            flash("There are no photos to show at that URL", category="flickr_url")
            return render_template("find_photos.html", form=form, flickr_url=url)

        return redirect(url_for("select_photos", flickr_url=url))

    # We may be redirected back to this page if something went wrong
    # at the "select photos" step, e.g. if the URL looks like a valid
    # Flickr URL but is actually a 404.
    #
    # In that case, we want to prefill the form with the URL the user
    # entered previously, if they want to edit it and try again.
    flickr_url = session.pop("flickr_url", "")

    return render_template("find_photos.html", form=form, flickr_url=flickr_url)


class FlickrPhotoURLForm(FlaskForm):
    """
    A form with a single input field where the user can enter a Flickr URL.
    """

    flickr_url = URLField(validators=[DataRequired()])

    submit = SubmitField("Go")
