import bs4
from flask import render_template
import pytest

from utils import minify


EMPTY_DATA = {
    "duplicates": {},
    "disallowed_licenses": {},
    "restricted": set(),
    "available": [],
}


def get_paragraphs(html):
    soup = bs4.BeautifulSoup(html, "html.parser")

    result = []

    for paragraph in soup.find_all("p"):
        p_class = paragraph.attrs["class"][0]
        text = minify(paragraph.getText())

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
        "select_photos/which_photos_can_be_uploaded.html",
        photos={
            **EMPTY_DATA,
            "available": [f"photo-{i}" for i in range(count)],
        },
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
        "select_photos/which_photos_can_be_uploaded.html",
        photos={
            **EMPTY_DATA,
            "duplicates": {
                f"photo-{i}": {"id": "M1234", "title": "File:duplicate"}
                for i in range(count)
            },
        },
    )

    assert get_paragraphs(html) == [
        {"class": "message_duplicate", "text": expected_text},
    ]


@pytest.mark.parametrize(
    ["count", "expected_text"],
    [
        (1, "This photo can’t be used because it has a CC BY-NC 2.0 license."),
        (
            2,
            "Neither of these photos can be used because they have CC BY-NC 2.0 licenses.",
        ),
        (
            3,
            "None of these photos can be used because they have CC BY-NC 2.0 licenses.",
        ),
        (
            10,
            "None of these photos can be used because they have CC BY-NC 2.0 licenses.",
        ),
    ],
)
def test_shows_correct_message_when_all_disallowed(app, count, expected_text):
    """
    Every photo has a CC-BY 2.0 license which isn't allowed on Commons.
    """
    html = render_template(
        "select_photos/which_photos_can_be_uploaded.html",
        photos={
            **EMPTY_DATA,
            "disallowed_licenses": {f"photo-{i}": "CC BY-NC 2.0" for i in range(count)},
        },
    )

    assert get_paragraphs(html) == [
        {
            "class": "message_disallowed",
            "text": f"{expected_text} "
            + "Wikimedia Commons only accepts CC0, CC BY, CC BY-SA, and Public Domain photos that are also public and safe on Flickr.",
        },
    ]


@pytest.mark.parametrize(
    ["count", "expected_text"],
    [
        (1, "This photo can’t be used."),
        (2, "Neither of these photos can be used."),
        (3, "None of these photos can be used."),
        (10, "None of these photos can be used."),
    ],
)
def test_shows_correct_message_when_all_restricted(app, count, expected_text):
    """
    Every photo has a CC-BY 2.0 license which isn't allowed on Commons.
    """
    html = render_template(
        "select_photos/which_photos_can_be_uploaded.html",
        photos={
            **EMPTY_DATA,
            "restricted": {f"photo-{i}": "CC BY-NC 2.0" for i in range(count)},
        },
    )

    assert get_paragraphs(html) == [
        {
            "class": "message_disallowed",
            "text": expected_text
            + " Wikimedia Commons only accepts CC0, CC BY, CC BY-SA, and Public Domain photos that are also public and safe on Flickr.",
        },
    ]


@pytest.mark.parametrize(
    ["licenses", "expected_text"],
    [
        (
            ["CC BY-NC 2.0", "CC BY-ND 2.0", "CC BY-NC 2.0"],
            "None of these photos can be used because they have CC BY-NC 2.0 and CC BY-ND 2.0 licenses.",
        ),
        (
            ["All Rights Reserved"],
            "This photo can’t be used because it has an All Rights Reserved license.",
        ),
        (
            ["All Rights Reserved", "CC BY-NC 2.0", "CC BY-ND 2.0"],
            "None of these photos can be used because they have All Rights Reserved, CC BY-NC 2.0 and CC BY-ND 2.0 licenses.",
        ),
    ],
)
def test_shows_correct_combination_of_licenses(app, licenses, expected_text):
    html = render_template(
        "select_photos/which_photos_can_be_uploaded.html",
        photos={
            **EMPTY_DATA,
            "disallowed_licenses": {
                f"photo-{i}": lic for i, lic in enumerate(licenses)
            },
        },
    )

    assert get_paragraphs(html) == [
        {
            "class": "message_disallowed",
            "text": expected_text
            + " Wikimedia Commons only accepts CC0, CC BY, CC BY-SA, and Public Domain photos that are also public and safe on Flickr.",
        },
    ]


@pytest.mark.parametrize(
    ["available", "expected_available_text"],
    [
        (0, None),
        (1, "One of these photos can be uploaded to Wikimedia Commons. Yay!"),
        (2, "2 of these photos can be uploaded to Wikimedia Commons. Yay!"),
        (3, "3 of these photos can be uploaded to Wikimedia Commons. Yay!"),
        (10, "10 of these photos can be uploaded to Wikimedia Commons. Yay!"),
    ],
)
@pytest.mark.parametrize(
    ["duplicates", "expected_duplicate_text"],
    [
        (0, None),
        (
            1,
            "Some of your work is done! One photo is already in Wikimedia Commons. W00t!",
        ),
        (
            2,
            "Some of your work is done! 2 photos are already in Wikimedia Commons. W00t!",
        ),
        (
            3,
            "Some of your work is done! 3 photos are already in Wikimedia Commons. W00t!",
        ),
        (
            10,
            "Some of your work is done! 10 photos are already in Wikimedia Commons. W00t!",
        ),
    ],
)
@pytest.mark.parametrize(
    ["disallowed_licenses", "expected_disallowed_licenses_text"],
    [
        (0, None),
        (1, "One photo can’t be used because it has a CC BY-NC 2.0 license."),
        (2, "2 photos can’t be used because they have CC BY-NC 2.0 licenses."),
        (3, "3 photos can’t be used because they have CC BY-NC 2.0 licenses."),
        (10, "10 photos can’t be used because they have CC BY-NC 2.0 licenses."),
    ],
)
@pytest.mark.parametrize("restricted", [0, 1])
def test_shows_correct_message(
    app,
    available,
    duplicates,
    disallowed_licenses,
    restricted,
    expected_available_text,
    expected_duplicate_text,
    expected_disallowed_licenses_text,
):
    # This test is explicitly for cases where we have a mixed collection
    # of photos; any time the parameters give us a single type of photo,
    # we want to skip.
    if (
        (available == 0 and duplicates == 0)
        or (duplicates == 0 and disallowed_licenses == 0)
        or (disallowed_licenses == 0 and available == 0)
    ):
        pytest.skip("invalid parameter combination")

    html = render_template(
        "select_photos/which_photos_can_be_uploaded.html",
        photos={
            "available": [f"photo-{i}" for i in range(available)],
            "duplicates": {
                f"photo-{i}": {"id": f"M{i}", "title": "dupe"}
                for i in range(duplicates)
            },
            "disallowed_licenses": {
                f"photo-{i}": "CC BY-NC 2.0" for i in range(disallowed_licenses)
            },
            "restricted": {f"photo-{i}" for i in range(restricted)},
        },
    )

    expected = []

    if available > 0:
        expected.append(
            {
                "class": "message_available",
                "text": expected_available_text,
            }
        )

    if duplicates > 0:
        expected.extend(
            [
                {"class": "message_duplicate", "text": expected_duplicate_text},
            ]
        )

    if disallowed_licenses > 0:
        expected.extend(
            [
                {
                    "class": "message_disallowed",
                    "text": expected_disallowed_licenses_text
                    + " Wikimedia Commons only accepts CC0, CC BY, CC BY-SA, and Public Domain photos that are also public and safe on Flickr.",
                },
            ]
        )

    assert get_paragraphs(html) == expected
