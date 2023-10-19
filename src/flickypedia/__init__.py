from flask import Flask, render_template

from flickypedia.auth import (db, login,     logout,
    oauth2_authorize_wikimedia,
    oauth2_callback_wikimedia,)
from flickypedia.config import Config
from flickypedia.tasks import celery_init_app


def homepage():
    return render_template("homepage.html")


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login.init_app(app)

    celery_app = celery_init_app(app)

    app.add_url_rule("/", view_func=homepage)

    app.add_url_rule("/logout", view_func=logout)
    app.add_url_rule("/authorize/wikimedia", view_func=oauth2_authorize_wikimedia)
    app.add_url_rule("/callback/wikimedia", view_func=oauth2_callback_wikimedia)

    return app


app = create_app()
