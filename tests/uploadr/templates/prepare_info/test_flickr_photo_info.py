import re
import typing

import bs4
from flask import Flask, render_template
from flickr_api.models import User as FlickrUser
import pytest


EMPTY_INFO: typing.Any = {
    "owner": {
        "username": "example",
        "realname": "example",
        "profile_url": "https://www.flickr.com/people/example",
    },
    "license": {"label": "CC BY 2.0"},
    "title": None,
    "description": None,
}


class MetadataEntry(typing.TypedDict):
    key: str
    value: str | None


def get_metadata(photo: typing.Any) -> list[MetadataEntry]:
    html = render_template(
        "prepare_info/flickr_photo_info.html", photo={**EMPTY_INFO, **photo}
    )

    soup = bs4.BeautifulSoup(html, "html.parser")

    result: list[MetadataEntry] = []

    for elem in soup.find("dl").children:  # type: ignore
        if elem == "\n":
            continue

        if elem.name == "dt":  # type: ignore
            result.append({"key": elem.text.strip(), "value": None})
        elif elem.name == "dd":  # type: ignore
            text = elem.text.strip()
            text = re.sub(r"\s*\n\s*", "\n", text)
            while "  " in text:
                text = text.replace("  ", " ")
            result[-1]["value"] = text
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
                "profile_url": "https://www.flickr.com/people/obamawhitehouse",
            },
            "Obama White House Archived",
        ),
        (
            {
                "username": "George",
                "realname": "George Oates",
                "profile_url": "https://www.flickr.com/people/george",
            },
            "George Oates",
        ),
    ],
)
def test_it_shows_the_correct_owner_name(
    app: Flask, owner: FlickrUser, expected_name: str
) -> None:
    metadata = get_metadata(photo={"owner": owner})

    assert metadata[0] == {"key": "By:", "value": f"{expected_name}\nCC BY 2.0"}


def test_it_shows_the_title(app: Flask) -> None:
    metadata = get_metadata(
        photo={
            "title": "A photo of some autumn leaves",
        }
    )

    assert {"key": "Title:", "value": "A photo of some autumn leaves"} in metadata


class Description(typing.TypedDict):
    input: str
    expected_key: str
    expected_value: str


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
            "input": "a" * 130 + " and now we have some words to push us over",
            "expected_key": "Description (excerpt):",
            "expected_value": "a" * 130 + " and now we have some […]",
        },
    ],
)
def test_it_shows_the_description(app: Flask, description: Description) -> None:
    metadata = get_metadata(photo={"description": description["input"]})

    assert {
        "key": description["expected_key"],
        "value": description["expected_value"],
    } in metadata


def test_it_omits_title_and_description_if_empty(app: Flask) -> None:
    metadata = get_metadata(
        photo={
            "title": None,
            "description": None,
        }
    )

    assert len(metadata) == 1
    assert not any(m["key"] == "Title:" for m in metadata)
    assert not any(m["key"] == "Description:" for m in metadata)
