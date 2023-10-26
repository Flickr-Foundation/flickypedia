"""
A page where a user is shown a list of photos they've chosen,
and they have to add title/caption/other metadata

    - photo 1: title ____ / caption ____ / categories ____
    - photo 2: title ____ / caption ____ / categories ____
    - photo 3: title ____ / caption ____ / categories ____

This page gets two arguments as query parameters:

-   A comma-separated list of photo IDs in ``selected_photo_ids``
-   A pointer to a cached Flickr API response in ``cached_api_response_id``

"""

from flask import render_template
from flask_login import login_required


@login_required
def prepare_info():
    return render_template("prepare_info.html", current_step="prepare_info")
