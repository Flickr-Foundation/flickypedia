"""
Create Wikitext for display on Wikimedia Commons.

Note that we primarily rely on structured data to put information on
the page using the Lua-driven {{Information}} template, so we don't
need to put in much text ourself.

== Useful reading ==

*   Help:Wikitext
    https://en.wikipedia.org/wiki/Help:Wikitext

"""

import datetime

from flickr_photos_api import SinglePhoto


def create_wikitext(photo: SinglePhoto, wikimedia_user_name: str) -> str:
    """
    Creates the Wikitext for a Flickr photo being uploaded to Wiki Commons.

    We add three templates:

    -   The {{Information}} template adds a table with some key info
        populated from the structured data (e.g. source URL, creator)
    -   The {{license}} template adds an info box describing the terms
        of the license of this photo.
    -   The {{Uploaded with Flickypedia}} template adds an info box explaining
        when and how this photo was copied from Flickr.

    See:
    https://commons.wikimedia.org/wiki/Template:Information
    https://commons.wikimedia.org/wiki/Template:Cc-by-2.0
    https://commons.wikimedia.org/wiki/Template:Uploaded_with_Flickypedia

    """

    license_id = photo["license"]["id"]
    owner = photo["owner"]

    lines = [
        "=={{int:filedesc}}==",
        "{{Information}}",
        "",
        "=={{int:license-header}}==",
        "{{%s}}" % license_id,
        "",
        "{{Uploaded with Flickypedia" "|user=%s" % wikimedia_user_name,
        "|date=%s" % datetime.datetime.now().strftime("%Y-%m-%d"),
        "|flickrUser=%s" % owner["realname"] or owner["username"],
        "|flickrUserUrl=%s" % owner["profile_url"],
        "|flickrPhotoUrl=%s" % photo["url"],
        "}}",
    ]

    return "\n".join(lines)
