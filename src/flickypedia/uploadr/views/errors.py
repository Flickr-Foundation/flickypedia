from flask import render_template


def not_found(e: Exception) -> tuple[str, int]:
    return render_template("not_found.html"), 404
