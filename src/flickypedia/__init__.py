from flask import Flask

from flickypedia.config import Config


app = Flask(__name__)
app.config.from_object(Config)

from flickypedia import routes  # noqa: E402, F401
