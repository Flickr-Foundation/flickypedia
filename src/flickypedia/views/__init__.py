from flask import render_template

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


__all__ = [
    "about",
    "bookmarklet",
    "get_photos",
    "get_upload_status",
    "homepage",
    "prepare_info",
    "select_photos",
    "wait_for_upload",
]
