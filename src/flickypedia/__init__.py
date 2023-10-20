from flask import Flask, render_template

from flickypedia.auth import (
    db,
    login,
    logout,
    oauth2_authorize_wikimedia,
    oauth2_callback_wikimedia,
)
from flickypedia.config import Config
from flickypedia.pages import find_photos, prepare_info, select_photos
from flickypedia.tasks import celery_init_app
from flickypedia.utils import a_href


def homepage():
    return render_template("homepage.html")


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login.init_app(app)
    celery_init_app(app)

    with app.app_context():
        db.create_all()

    app.add_url_rule("/", view_func=homepage)

    app.add_url_rule("/logout", view_func=logout)
    app.add_url_rule("/authorize/wikimedia", view_func=oauth2_authorize_wikimedia)
    app.add_url_rule("/callback/wikimedia", view_func=oauth2_callback_wikimedia)

    app.add_url_rule("/find_photos", view_func=find_photos, methods=["GET", "POST"])
    app.add_url_rule("/select_photos", view_func=select_photos, methods=["GET", "POST"])
    app.add_url_rule("/prepare_info", view_func=prepare_info, methods=["GET", "POST"])

    app.jinja_env.filters["a_href"] = a_href

    @app.template_filter()
    def image_at(sizes, desired_size):
        """
        Given a list of image sizes from the Flickr API, return the source URL of
        the desired size.
        """
        # TODO: Make more rigorous.  This function is very basic, and will throw
        # a StopIteration exception if the size isn't found.
        #
        # It would be better if it had an awareness of the sizes that the Flickr API
        # might return, so it could
        return next(s["source"] for s in sizes if s["label"] == desired_size)

    return app
