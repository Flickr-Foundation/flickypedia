import re

import bs4
from flask import render_template
import pytest


EMPTY_INFO = {
    "owner": {"username": "example", "realname": "example"},
    "license": {"label": "CC BY 2.0"},
    "title": None,
    "description": None,
}


def get_metadata(photo):
    html = render_template(
        "components/prepare_info_flickr_photo_info.html", photo={**EMPTY_INFO, **photo}
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
    metadata = get_metadata(photo={"owner": owner})

    assert metadata[0] == {"key": "By:", "value": f"{expected_name}\nCC BY 2.0"}


def test_it_shows_the_title(app):
    metadata = get_metadata(
        photo={
            "title": "A photo of some autumn leaves",
        }
    )

    assert {"key": "Title:", "value": "A photo of some autumn leaves"} in metadata


@pytest.mark.parametrize(
    "description",
    [
        {
            "input": "Red, gold, and orange leaves lying on the ground",
            "expected_key": "Description:",
            "expected_value": "Red, gold, and orange leaves lying on the ground",
        },
        # A test for escaping HTML entities
        {
            "input": "It pulls coaches of the 1960s &quot;Rheingold&quot; Express again.",
            "expected_key": "Description:",
            "expected_value": 'It pulls coaches of the 1960s "Rheingold" Express again.',
        },
        # A test for truncation
        {
            "input": "a" * 150 + " and now we have some words to push us over",
            "expected_key": "Description (excerpt):",
            "expected_value": "a" * 150 + " and now we have some…",
        },
    ],
)
def test_it_shows_the_description(app, description):
    metadata = get_metadata(photo={"description": description["input"]})

    assert {
        "key": description["expected_key"],
        "value": description["expected_value"],
    } in metadata


def test_it_omits_title_and_description_if_empty(app):
    metadata = get_metadata(
        photo={
            "title": None,
            "description": None,
        }
    )

    assert len(metadata) == 1
    assert not any(m["key"] == "Title:" for m in metadata)
    assert not any(m["key"] == "Description:" for m in metadata)
