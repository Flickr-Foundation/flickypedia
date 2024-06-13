from flickypedia.apis.flickr import (
    create_bot_comment_text,
    create_default_user_comment_text,
)


def test_create_bot_comment_text() -> None:
    actual = create_bot_comment_text(
        user_url="https://commons.wikimedia.org/wiki/User:Alexwlchan",
        user_name="Alexwlchan",
        wikimedia_page_title="File:London_Bridge_At_Night.jpg",
    )

    expected = """Hi, I’m <a href="https://www.flickr.com/people/flickypedia">Flickypedia Bot</a>.

A Wikimedia Commons user named <a href="https://commons.wikimedia.org/wiki/User:Alexwlchan">Alexwlchan</a> has uploaded your photo to <a href="https://commons.wikimedia.org/wiki/Main_Page">Wikimedia Commons</a>.

<a href="https://commons.wikimedia.org/wiki/File:London_Bridge_At_Night.jpg">Would you like to see</a>? We hope you like it!"""

    assert actual == expected


def test_create_default_user_comment_text() -> None:
    actual = create_default_user_comment_text(
        wikimedia_page_title="File:London_Bridge_At_Night.jpg"
    )

    expected = """Hi, I’ve uploaded your photo to <a href="https://commons.wikimedia.org/wiki/Main_Page">Wikimedia Commons</a>. <a href="https://commons.wikimedia.org/wiki/File:London_Bridge_At_Night.jpg">Would you like to see</a>?

I hope you like it!"""

    assert actual == expected
