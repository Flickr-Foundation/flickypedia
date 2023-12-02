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


def create_wikitext(license_id: str) -> str:
    """
    Creates the Wikitext for a Flickr photo being uploaded to Wiki Commons.
    """
    license_template_name = LICENSE_TEMPLATE_MAPPING[license_id]

    lines = [
        "=={{int:filedesc}}==",
        "{{Information}}",
        "",
        "=={{int:license-header}}==",
        "{{%s}}" % license_template_name,
    ]

    return "\n".join(lines)
