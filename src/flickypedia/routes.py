from flask import render_template, jsonify

from flickypedia import app
from flickypedia.auth import (
    logout,
    oauth2_authorize_wikimedia,
    oauth2_callback_wikimedia,
)


app.add_url_rule("/logout", view_func=logout)
app.add_url_rule("/authorize/wikimedia", view_func=oauth2_authorize_wikimedia)
app.add_url_rule("/callback/wikimedia", view_func=oauth2_callback_wikimedia)


@app.route("/")
def index():
    return render_template("index.html")


from celery import shared_task
from celery.result import AsyncResult


@shared_task(ignore_result=False)
def add_together(a: int, b: int) -> int:
    print(f"working on task {celery.current_task.request.id}")
    print(f"result = {a + b}")
    return a + b


@app.route("/go")
def go():
    result = add_together.delay(1, 2)
    return f"Go! {result.id}"


@app.route("/result/<id>")
def task_result(id: str) -> dict[str, object]:
    result = AsyncResult(id)
    return jsonify(
        {
            "ready": result.ready(),
            "successful": result.successful(),
            "value": result.result if result.ready() else None,
        }
    )
