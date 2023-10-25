import re

import bs4
from flask import render_template
import pytest


def get_paragraphs(html):
    soup = bs4.BeautifulSoup(html, "html.parser")

    result = []

    for paragraph in soup.find_all("p"):
        p_class = paragraph.attrs["class"][0]
        text = re.sub(r"\s+", " ", paragraph.getText()).strip()

        result.append({"class": p_class, "text": text})

    return result


@pytest.mark.parametrize(
    ["count", "expected_text"],
    [
        (1, "This photo can be uploaded to Wikimedia Commons. Yay!"),
        (2, "Both photos can be uploaded to Wikimedia Commons. Yay!"),
        (3, "All 3 photos can be uploaded to Wikimedia Commons. Yay!"),
        (10, "All 10 photos can be uploaded to Wikimedia Commons. Yay!"),
    ],
)
def test_shows_correct_message_when_all_available(app, count, expected_text):
    """
    Every photo can be uploaded to Wikimedia Commons.
    """
    html = render_template(
        "components/select_photos_message.html",
        photos={"available": [f"photo-{i}" for i in range(count)]},
    )

    assert get_paragraphs(html) == [
        {
            "class": "message_available",
            "text": expected_text,
        }
    ]


@pytest.mark.parametrize(
    ["count", "expected_text"],
    [
        (1, "Your work is done! This photo is already in Wikimedia Commons. W00t!"),
        (2, "Your work is done! Both photos are already in Wikimedia Commons. W00t!"),
        (3, "Your work is done! All 3 photos are already in Wikimedia Commons. W00t!"),
        (
            10,
            "Your work is done! All 10 photos are already in Wikimedia Commons. W00t!",
        ),
    ],
)
def test_shows_correct_message_when_all_duplicates(app, count, expected_text):
    """
    Every photo is a duplicate of one already on Commons.
    """
    html = render_template(
        "components/select_photos_message.html",
        photos={"duplicates": {f"photo-{i}": "dupe" for i in range(count)}},
    )

    assert get_paragraphs(html) == [
        {"class": "message_duplicate", "text": expected_text},
        {"class": "duplicate_link", "text": "Have a look?"},
    ]
