from flask import render_template
from flask_login import login_required


@login_required
def find_photos():
    return render_template("find_photos.html")
