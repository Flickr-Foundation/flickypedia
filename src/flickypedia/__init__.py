from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from flickypedia.config import Config
from flickypedia.tasks import celery_init_app


app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

celery_app = celery_init_app(app)

from flickypedia import auth  # noqa: E402, F401
from flickypedia import routes  # noqa: E402, F401
