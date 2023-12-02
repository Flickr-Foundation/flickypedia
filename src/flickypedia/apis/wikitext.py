"""
Create Wikitext for display on Wikimedia Commons.

Note that we primarily rely on structured data to put information on
the page using the Lua-driven {{Information}} template, so we don't
need to put in much text ourself.

== Useful reading ==

*   Help:Wikitext
    https://en.wikipedia.org/wiki/Help:Wikitext

"""


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


def create_wikitext(license_id: str, new_categories: list[str]) -> str:
    """
    Creates the Wikitext for a Flickr photo being uploaded to Wiki Commons.
    """
    information = "=={{int:filedesc}}==\n" "{{Information}}"

    license = (
        "=={{int:license-header}}==\n" "{{%s}}" % LICENSE_TEMPLATE_MAPPING[license_id]
    )

    categories = "\n".join(
        f"[[Category:{category_name}]]" for category_name in new_categories
    )

    return "\n\n".join([information, license, categories]).strip()
