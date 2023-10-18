import datetime

import pytest

from flickypedia.apis.wikitext import create_wikitext


def test_create_wikitext_for_regular_photo():
    actual = create_wikitext(
        photo_url="https://www.flickr.com/photos/199246608@N02/53255367525/",
        date_taken={
            "value": datetime.datetime(2023, 10, 11, 11, 49, 25),
            "unknown": False,
            "granularity": 0,
        },
        flickr_user={
            "id": "199246608@N02",
            "username": "cefarrjf87",
            "realname": "Alex Chan",
        },
        license_id="cc-by-2.0",
    )
    expected = """=={{int:filedesc}}==
{{Information
|Source=https://www.flickr.com/photos/199246608@N02/53255367525/
|Date=2023-10-11 11:49:25
|Author=[https://www.flickr.com/people/199246608@N02 Alex Chan]
|Permission=
|other_versions=
}}

=={{int:license-header}}==
{{cc-by-2.0}}
"""

    assert actual == expected


@pytest.mark.parametrize(
    ["date_taken", "expected_date_text"],
    [
        (
            {
                "value": datetime.datetime(2001, 2, 3, 4, 5, 6),
                "unknown": False,
                "granularity": 0,  # Day
            },
            "|Date=2001-02-03 04:05:06\n",
        ),
        (
            {
                "value": datetime.datetime(2001, 2, 3, 4, 5, 6),
                "unknown": False,
                "granularity": 4,  # Month
            },
            "|Date=2001-02\n",
        ),
        (
            {
                "value": datetime.datetime(2001, 2, 3, 4, 5, 6),
                "unknown": False,
                "granularity": 6,  # Year
            },
            "|Date=2001\n",
        ),
        (
            {
                "value": datetime.datetime(2001, 2, 3, 4, 5, 6),
                "unknown": False,
                "granularity": 8,  # Circa
            },
            "|Date={{circa|2001}}\n",
        ),
        (
            {
                "value": datetime.datetime(2001, 2, 3, 4, 5, 6),
                "unknown": True,
                "granularity": 0,  # Circa
            },
            "|Date={{Other date|?}}\n",
        ),
    ],
)
def test_create_wikitext_with_date_granularity(date_taken, expected_date_text):
    wikitext = create_wikitext(
        photo_url="https://www.flickr.com/photos/example/1234",
        date_taken=date_taken,
        flickr_user={"id": "1234", "username": "example", "realname": "example"},
        license_id="cc-by-2.0",
    )

    assert expected_date_text in wikitext


@pytest.mark.parametrize(
    ["flickr_user", "expected_author_text"],
    [
        (
            {
                "id": "199246608@N02",
                "username": "cefarrjf87",
                "realname": "Alex Chan",
            },
            "|Author=[https://www.flickr.com/people/199246608@N02 Alex Chan]",
        ),
        (
            {
                "id": "35591378@N03",
                "username": "Obama White House Archived",
                "realname": None,
            },
            "|Author=[https://www.flickr.com/people/35591378@N03 Obama White House Archived]",
        ),
    ],
)
def test_create_wikitext_with_user_info(flickr_user, expected_author_text):
    wikitext = create_wikitext(
        photo_url="https://www.flickr.com/photos/example/1234",
        date_taken={
            "value": datetime.datetime(2001, 2, 3, 4, 5, 6),
            "unknown": False,
            "granularity": 0,
        },
        flickr_user=flickr_user,
        license_id="cc-by-2.0",
    )

    assert expected_author_text in wikitext
