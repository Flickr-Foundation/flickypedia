import datetime

from flickypedia.apis.wikimedia import create_wikitext


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
|Source=[https://www.flickr.com/photos/199246608@N02/53255367525/]
|Date=2023-10-11 11:49
|Author=[https://www.flickr.com/people/199246608@N02 Alex Chan]
|Permission=
|other_versions=
}}

=={{int:license-header}}==
{{cc-by-2.0}}
"""

    assert actual == expected
