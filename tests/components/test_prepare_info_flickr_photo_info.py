import datetime
import re

import bs4
from flask import render_template
import pytest

from flickypedia.apis.structured_data import (
    create_copyright_status_statement,
    create_date_taken_statement,
    create_flickr_creator_statement,
    create_license_statement,
    create_posted_to_flickr_statement,
    create_source_data_for_photo,
)


def get_metadata(photo):
    html = render_template(
        "components/prepare_info_flickr_photo_info.html", photo=photo
    )

    soup = bs4.BeautifulSoup(html, "html.parser")

    result = []

    for elem in soup.find("dl").children:
        if elem == "\n":
            continue

        if elem.name == "dt":
            result.append({"key": elem.text.strip(), "value": None})
        elif elem.name == "dd":
            result[-1]["value"] = re.sub(r"\s*\n\s*", "\n", elem.text.strip())
        else:  # pragma: no cover
            raise ValueError(f"unrecognised element: {elem}")

    return result


@pytest.mark.parametrize(
    ["owner", "expected_name"],
    [
        (
            {
                "username": "Obama White House Archived",
                "realname": None,
            },
            "Obama White House Archived",
        ),
        ({"username": "George", "realname": "George Oates"}, "George Oates"),
    ],
)
def test_it_shows_the_correct_owner_name(app, owner, expected_name):
    metadata = get_metadata(
        photo={
            "owner": owner,
            "license": {"label": "CC BY 2.0"},
            "title": None,
            "description": None,
        }
    )

    assert metadata[0] == {"key": "By:", "value": f"{expected_name}\nCC BY 2.0"}


def test_it_shows_the_title(app):
    metadata = get_metadata(
        photo={
            "owner": {"username": "example", "realname": "example"},
            "license": {"label": "CC BY 2.0"},
            "title": "A photo of some autumn leaves",
            "description": None,
        }
    )

    assert {"key": "Title:", "value": "A photo of some autumn leaves"} in metadata


def test_it_shows_the_description(app):
    metadata = get_metadata(
        photo={
            "owner": {"username": "example", "realname": "example"},
            "license": {"label": "CC BY 2.0"},
            "title": None,
            "description": "Red, gold, and orange leaves lying on the ground",
        }
    )

    assert {
        "key": "Description:",
        "value": "Red, gold, and orange leaves lying on the ground",
    } in metadata


def test_it_omits_title_and_description_if_empty(app):
    metadata = get_metadata(
        photo={
            "owner": {"username": "example", "realname": "example"},
            "license": {"label": "CC BY 2.0"},
            "title": None,
            "description": None,
        }
    )

    assert len(metadata) == 1
    assert not any(m["key"] == "Title:" for m in metadata)
    assert not any(m["key"] == "Description:" for m in metadata)
