from flask import render_template

from .get_photos import get_photos
from .prepare_info import prepare_info
from .select_photos import select_photos


def homepage():
    return render_template("homepage.html")


__all__ = ["get_photos", "homepage", "prepare_info", "select_photos"]
