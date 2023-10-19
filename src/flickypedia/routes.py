from flask import render_template, jsonify

from flickypedia import app
from flickypedia.auth import (
    logout,
    oauth2_authorize_wikimedia,
    oauth2_callback_wikimedia,
)
from flickypedia.tasks import get_status, upload_images
from flickypedia.views.find_photos import find_photos
from flickypedia.views.prepare_info import prepare_info
from flickypedia.utils import a_href


app.add_url_rule("/logout", view_func=logout)
app.add_url_rule("/authorize/wikimedia", view_func=oauth2_authorize_wikimedia)
app.add_url_rule("/callback/wikimedia", view_func=oauth2_callback_wikimedia)

app.add_url_rule("/find_photos", methods=["GET", "POST"], view_func=find_photos)
app.add_url_rule("/prepare_info", methods=["GET", "POST"], view_func=prepare_info)

app.jinja_env.filters['a_href'] = a_href


@app.route("/")
def index():
    return render_template("homepage.html")


@app.route("/go")
def go():
    result = upload_images.delay(10)
    return f"Go! <a href='/result/{result.id}'>{result.id}</a>"


@app.route("/result/<task_id>")
def task_result(task_id: str):
    return jsonify(get_status(task_id=task_id))
