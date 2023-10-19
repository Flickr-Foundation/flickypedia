from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

from flickypedia.config import Config
from flickypedia.tasks import celery_init_app


def create_app(**kwargs):
    app = Flask(__name__, **kwargs)
    app.config.from_object(Config)

    from flickypedia.auth import (db, login, logout, oauth2_authorize_wikimedia, oauth2_callback_wikimedia)

    db.init_app(app)
    login.init_app(app)

    from flickypedia.views.find_photos import find_photos
    from flickypedia.views.prepare_info import prepare_info

    app.add_url_rule("/logout", view_func=logout)
    app.add_url_rule("/authorize/wikimedia", view_func=oauth2_authorize_wikimedia)
    app.add_url_rule("/callback/wikimedia", view_func=oauth2_callback_wikimedia)

    app.add_url_rule("/find_photos", methods=["GET", "POST"], view_func=find_photos)
    app.add_url_rule("/prepare_info", methods=["GET", "POST"], view_func=prepare_info)

    return app


app = create_app()

# db = SQLAlchemy(app)
# login = LoginManager(app)

celery_app = celery_init_app(app)

from flickypedia import auth  # noqa: E402, F401
from flickypedia import routes  # noqa: E402, F401
