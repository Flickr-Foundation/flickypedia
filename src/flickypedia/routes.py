from flask import render_template, jsonify

from flickypedia import app
from flickypedia.auth import (
    logout,
    oauth2_authorize_wikimedia,
    oauth2_callback_wikimedia,
)
from flickypedia.tasks import get_status, upload_images


app.add_url_rule("/logout", view_func=logout)
app.add_url_rule("/authorize/wikimedia", view_func=oauth2_authorize_wikimedia)
app.add_url_rule("/callback/wikimedia", view_func=oauth2_callback_wikimedia)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/go")
def go():
    result = upload_images.delay(10)
    return f"Go! <a href='/result/{result.id}'>{result.id}</a>"


@app.route("/result/<task_id>")
def task_result(task_id: str):
    return jsonify(get_status(task_id=task_id))
