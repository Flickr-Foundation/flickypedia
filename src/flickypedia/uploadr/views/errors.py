from flask import render_template


def unauthorized(e: Exception) -> tuple[str, int]:
    return render_template("unauthorized.html"), 401


def not_found(e: Exception) -> tuple[str, int]:
    return render_template("not_found.html"), 404
