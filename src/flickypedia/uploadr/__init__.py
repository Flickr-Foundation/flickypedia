import html
import os
import pathlib
import uuid

from flask import Flask, request
from jinja2 import StrictUndefined
import sass

from .auth import (
    login,
    logout,
    oauth2_authorize_wikimedia,
    oauth2_callback_wikimedia,
    user_db,
)
from .cli import uploadr as uploadr_cli
from .config import create_config, get_directories
from flickypedia.duplicates import create_link_to_commons
from flickypedia.photos import size_at
from flickypedia.apis.structured_data.wikidata import (
    get_entity_label,
    get_property_name,
    render_wikidata_date,
)
from .views import (
    about,
    bookmarklet,
    faqs,
    find_matching_categories_api,
    find_matching_languages_api,
    get_photos,
    get_upload_status,
    homepage,
    prepare_info,
    say_thanks,
    select_photos,
    truncate_description,
    validate_title_api,
    wait_for_upload,
    upload_complete,
)
from flickypedia.utils import create_bookmarklet


def create_app(
    data_directory: pathlib.Path = pathlib.Path("data"), debug: bool = False
) -> Flask:
    app = Flask(__name__)

    config = create_config(data_directory)

    app.config.update(**config)

    user_db.init_app(app)
    login.init_app(app)

    with app.app_context():
        user_db.create_all()

    for dirname in get_directories(app.config):
        os.makedirs(dirname, exist_ok=True)

    app.add_url_rule("/", view_func=homepage)

    app.add_url_rule("/logout", view_func=logout)
    app.add_url_rule("/authorize/wikimedia", view_func=oauth2_authorize_wikimedia)
    app.add_url_rule("/callback/wikimedia", view_func=oauth2_callback_wikimedia)

    app.add_url_rule("/get_photos", view_func=get_photos, methods=["GET", "POST"])
    app.add_url_rule("/select_photos", view_func=select_photos, methods=["GET", "POST"])
    app.add_url_rule("/prepare_info", view_func=prepare_info, methods=["GET", "POST"])
    app.add_url_rule("/wait_for_upload/<task_id>", view_func=wait_for_upload)
    app.add_url_rule("/wait_for_upload/<task_id>/status", view_func=get_upload_status)
    app.add_url_rule("/upload_complete/<task_id>", view_func=upload_complete)
    app.add_url_rule("/say_thanks/<task_id>", view_func=say_thanks)

    app.add_url_rule("/about/", view_func=about)
    app.add_url_rule("/bookmarklet/", view_func=bookmarklet)
    app.add_url_rule("/faqs/", view_func=faqs)

    app.add_url_rule("/api/validate_title", view_func=validate_title_api)
    app.add_url_rule(
        "/api/find_matching_categories", view_func=find_matching_categories_api
    )
    app.add_url_rule(
        "/api/find_matching_languages", view_func=find_matching_languages_api
    )

    app.jinja_env.filters["html_unescape"] = html.unescape
    app.jinja_env.filters["size_at"] = size_at
    app.jinja_env.filters["link_to_commons"] = create_link_to_commons
    app.jinja_env.filters["truncate_description"] = truncate_description
    app.jinja_env.filters["bookmarklet"] = create_bookmarklet

    app.jinja_env.filters["wikidata_property_name"] = get_property_name
    app.jinja_env.filters["wikidata_entity_label"] = get_entity_label
    app.jinja_env.filters["wikidata_date"] = render_wikidata_date

    # Compile the CSS.  If we're running in debug mode, rebuild it on
    # every request for convenience.
    static_folder: str = app.static_folder  # type: ignore

    compile_scss(static_folder)

    if debug:  # pragma: no cover

        @app.before_request
        def recompile_css() -> None:
            if request.path == "/static/style.css":
                compile_scss(static_folder)

    # This option causes Jinja to throw if we use an undefined variable
    # in one of the templates.
    # See https://alexwlchan.net/2022/strict-jinja/
    app.jinja_env.undefined = StrictUndefined

    # This causes Jinja to remove extraneous whitespace.
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    return app


def compile_scss(static_folder: str) -> None:
    """
    Compile the SCSS file into static.css.
    """
    sass_path = os.path.join(static_folder, "assets", "style.scss")
    css_path = os.path.join(static_folder, "style.css")

    # We want to write the CSS to a temporary file first, then atomically
    # rename it into place -- this avoids the server sending a user
    # a partially-complete CSS file.
    #
    # We give each temp file a unique name to avoid two different processes
    # trying to write to the same file.
    tmp_path = f"{css_path}.{uuid.uuid4()}.tmp"

    with open(tmp_path, "w") as out_file:
        out_file.write(sass.compile(filename=sass_path))

    os.rename(tmp_path, css_path)


__all__ = ["create_all", "uploadr_cli"]
