import os
import secrets

from flask import Flask, render_template
from flask_login import current_user


app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", secrets.token_hex())


@app.route("/")
def index():
    print(repr(current_user))
    return render_template("index.html", current_user=current_user)


from flickypedia import auth  # noqa: E402, F401
