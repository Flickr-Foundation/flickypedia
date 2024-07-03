from flask import Flask, render_template

from .api import (
    find_matching_categories_api,
    find_matching_languages_api,
    validate_title_api,
)
from . import errors
from .get_photos import get_photos
from .keep_going import keep_going
from .post_comments import post_comments, post_bot_comment_api, post_user_comment_api
from .prepare_info import prepare_info, truncate_description
from .say_thanks import say_thanks
from .select_photos import select_photos
from .wait_for_upload import get_upload_status, wait_for_upload
from .upload_complete import upload_complete


def homepage() -> str:
    return render_template("homepage.html")


def about() -> str:
    return render_template("about.html", current_step=None)


def bookmarklet() -> str:
    return render_template("bookmarklet.html", current_step=None)


def faqs() -> str:
    return render_template("faqs.html", current_step=None)


def register_views(app: Flask) -> None:
    app.register_error_handler(404, errors.not_found)


__all__ = [
    "about",
    "bookmarklet",
    "buddy_icon",
    "faqs",
    "find_matching_categories_api",
    "find_matching_languages_api",
    "get_photos",
    "get_upload_status",
    "homepage",
    "keep_going",
    "post_bot_comment_api",
    "post_user_comment_api",
    "post_comments",
    "prepare_info",
    "register_views",
    "say_thanks",
    "select_photos",
    "truncate_description",
    "validate_title_api",
    "wait_for_upload",
    "upload_complete",
]
