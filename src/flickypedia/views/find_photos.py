from flask import flash, redirect, render_template, url_for
from flask_wtf import FlaskForm
from flickr_url_parser import parse_flickr_url, NotAFlickrUrl, UnrecognisedUrl
from wtforms import URLField, SubmitField
from wtforms.validators import DataRequired


class FlickrPhotoURLForm(FlaskForm):
    flickr_url = URLField(validators=[DataRequired()])

    submit = SubmitField("Go")
    pass


def find_photos():
    form = FlickrPhotoURLForm()

    if form.validate_on_submit():
        url = form.flickr_url.data

        try:
            parse_flickr_url(url)
        except NotAFlickrUrl:
            flash("That doesn’t live on Flickr.com", category="flickr_url")
            return render_template("find_photos.html", form=form)
        except UnrecognisedUrl:
            flash("There are no photos to show at that URL", category="flickr_url")
            return render_template("find_photos.html", form=form)

        return redirect(url_for("prepare_info", flickr_url=url))

    return render_template("find_photos.html", form=form)
