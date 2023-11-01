from flask import abort, current_app, jsonify, render_template, request

from flickypedia.apis.wikimedia import WikimediaPublicApi
from .get_photos import get_photos
from .prepare_info import prepare_info
from .select_photos import select_photos
from .wait_for_upload import get_upload_status, wait_for_upload


def homepage():
    return render_template("homepage.html")


def about():
    return render_template("about.html", current_step=None)


def bookmarklet():
    return render_template("bookmarklet.html", current_step=None)


def validate_title():
    try:
        title = request.args['title']
    except KeyError:
        abort(400)

    api = WikimediaPublicApi(user_agent=current_app.config['USER_AGENT'])

    return jsonify(api.validate_title(title=title))


__all__ = [
    "about",
    "bookmarklet",
    "get_photos",
    "get_upload_status",
    "homepage",
    "prepare_info",
    "select_photos",
    "validate_title",
    "wait_for_upload",
]
