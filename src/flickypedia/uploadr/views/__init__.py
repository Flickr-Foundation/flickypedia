from flask import render_template

from .api import (
    find_matching_categories_api,
    find_matching_languages_api,
    validate_title_api,
)
from .get_photos import get_photos
from .prepare_info import prepare_info, truncate_description
from .say_thanks import say_thanks
from .select_photos import select_photos
from .wait_for_upload import get_upload_status, wait_for_upload
from .upload_complete import upload_complete
from ._types import ViewResponse


def homepage() -> ViewResponse:
    return render_template("homepage.html")


def about() -> ViewResponse:
    return render_template("about.html", current_step=None)


def bookmarklet() -> ViewResponse:
    return render_template("bookmarklet.html", current_step=None)


__all__ = [
    "about",
    "bookmarklet",
    "find_matching_categories_api",
    "find_matching_languages_api",
    "get_photos",
    "get_upload_status",
    "homepage",
    "prepare_info",
    "say_thanks",
    "select_photos",
    "truncate_description",
    "validate_title_api",
    "wait_for_upload",
    "upload_complete",
]
