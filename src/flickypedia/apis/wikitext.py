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

from flickypedia.apis.flickr_photos_api import SinglePhoto


# This maps our license IDs into the names of Wikimedia templates.
LICENSE_TEMPLATE_MAPPING = {
    # https://commons.wikimedia.org/wiki/Template:Cc-by-2.0
    "cc-by-2.0": "Cc-by-2.0",
    # https://commons.wikimedia.org/wiki/Template:Cc-by-sa-2.0
    "cc-by-sa-2.0": "Cc-by-sa-2.0",
    # https://en.wikipedia.org/wiki/Template:CC0
    "cc0-1.0": "CC0",
    "pdm": "CC0",
    # https://commons.wikimedia.org/wiki/Template:PD-USGov
    "usgov": "PD-USGov",
}


def create_wikitext(
    photo: SinglePhoto, wikimedia_username: str, new_categories: list[str]
) -> str:
    """
    Creates the Wikitext for a Flickr photo being uploaded to Wiki Commons.
    """
    # Add the Information template.  We don't need to set any values
    # here, because it'll be populated by the structured data.
    # See https://commons.wikimedia.org/wiki/Template:Information
    # fmt: off
    information = (
        "=={{int:filedesc}}==\n"
        "{{Information}}"
    )
    # fmt: on

    # Add a license heading and license info box.  This will be
    # internationalised as appropriate.
    # See https://commons.wikimedia.org/wiki/Template:License-header
    license = (
        "=={{int:license-header}}==\n"
        "{{%s}}" % LICENSE_TEMPLATE_MAPPING[photo["license"]["id"]]
    )

    # Add an info box about using Flickypedia.
    # See https://commons.wikimedia.org/wiki/Template:Uploaded_with_Flickypedia
    flickypedia = (
        "{{Uploaded with Flickypedia"
        "|user=%s\n"
        "|date=%s\n"
        "|flickrUser=%s\n"
        "|flickrUserUrl=%s\n"
        "|flickrPhotoUrl=%s\n"
        "}}"
    ) % (
        wikimedia_username,
        datetime.datetime.now().strftime("%Y-%m-%d"),
        photo["owner"]["realname"] or photo["owner"]["username"],
        photo["owner"]["profile_url"],
        photo["url"],
    )

    # Add a list of user-defined categories.
    categories = "\n".join(
        f"[[Category:{category_name}]]" for category_name in new_categories
    )

    return "\n\n".join([information, license, flickypedia, categories]).strip()
