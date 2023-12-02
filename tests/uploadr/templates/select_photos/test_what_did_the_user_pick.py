import bs4
from flask import Flask, render_template
from flickypedia.apis.flickr_photos_api import AlbumInfo
import pytest

from utils import minify


def get_text(html: str) -> str:
    soup = bs4.BeautifulSoup(html, "html.parser")

    return minify(soup.find("h2").getText().strip())  # type: ignore


@pytest.mark.parametrize(
    ["has_available_photos", "album", "expected_text"],
    [
        (
            True,
            {
                "owner": {
                    "realname": "Al Jazeera English",
                    "username": "Al Jazeera English",
                },
                "title": "Faces from the Libyan front",
            },
            "You’re looking at Al Jazeera English’s album called “Faces from the Libyan front”.",
        ),
        (
            False,
            {
                "owner": {
                    "realname": "Al Jazeera English",
                    "username": "Al Jazeera English",
                },
                "title": "Faces from the Libyan front",
            },
            "You looked up Al Jazeera English’s album called “Faces from the Libyan front”.",
        ),
    ],
)
def test_gets_an_album_description(
    app: Flask, has_available_photos: bool, album: AlbumInfo, expected_text: str
) -> None:
    html = render_template(
        "select_photos/what_did_the_user_pick.html",
        parsed_url={"type": "album"},
        photos={
            "available": [
                f"photo-{i}" for i in range(1 if has_available_photos else 0)
            ],
        },
        photo_data={
            "album": album,
        },
    )

    text = get_text(html)

    assert text == expected_text
