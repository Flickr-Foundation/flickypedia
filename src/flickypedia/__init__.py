import os

from flask import Flask
from jinja2 import StrictUndefined

from flickypedia.auth import (
    db,
    login,
    logout,
    oauth2_authorize_wikimedia,
    oauth2_callback_wikimedia,
)
from flickypedia.apis.wikidata import (
    get_entity_label,
    get_property_name,
    render_wikidata_date,
)
from flickypedia.config import create_config, get_directories
from flickypedia.duplicates import create_link_to_commons
from flickypedia.views import find_photos, homepage, prepare_info, select_photos
from flickypedia.tasks import celery_init_app
from flickypedia.utils import a_href, size_at


def create_app(data_directory):
    app = Flask(__name__)

    config = create_config(data_directory)

    app.config.update(**config)

    db.init_app(app)
    login.init_app(app)
    celery_init_app(app)

    with app.app_context():
        db.create_all()

    for dirname in get_directories(app.config):
        os.makedirs(dirname, exist_ok=True)

    app.add_url_rule("/", view_func=homepage)

    app.add_url_rule("/logout", view_func=logout)
    app.add_url_rule("/authorize/wikimedia", view_func=oauth2_authorize_wikimedia)
    app.add_url_rule("/callback/wikimedia", view_func=oauth2_callback_wikimedia)

    app.add_url_rule("/find_photos", view_func=find_photos, methods=["GET", "POST"])
    app.add_url_rule("/select_photos", view_func=select_photos, methods=["GET", "POST"])
    app.add_url_rule("/prepare_info", view_func=prepare_info, methods=["GET", "POST"])

    app.jinja_env.filters["a_href"] = a_href
    app.jinja_env.filters["size_at"] = size_at
    app.jinja_env.filters["link_to_commons"] = create_link_to_commons

    app.jinja_env.filters["wikidata_property_name"] = get_property_name
    app.jinja_env.filters["wikidata_entity_label"] = get_entity_label
    app.jinja_env.filters["wikidata_date"] = render_wikidata_date

    # This option causes Jinja to throw if we use an undefined variable
    # in one of the templates.
    # See https://alexwlchan.net/2022/strict-jinja/
    app.jinja_env.undefined = StrictUndefined

    # This causes Jinja to remove extraneous whitespace.
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    return app
