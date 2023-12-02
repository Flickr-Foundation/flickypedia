import pathlib
import textwrap

import pytest

from flickypedia.apis.flickr_photos_api import SinglePhoto
from flickypedia.apis.wikitext import create_wikitext
from flickypedia.uploadr.config import create_config
from utils import get_typed_fixture


def tidy(s: str) -> str:
    return textwrap.dedent(s).strip()


def test_create_wikitext_for_photo() -> None:
    photo = get_typed_fixture(
        "flickr_api/single_photo-4452100167.json", model=SinglePhoto
    )
    photo["license"]["id"] = "cc-by-2.0"

    actual = create_wikitext(photo, wikimedia_username="TestUser", new_categories=[])
    expected = tidy(
        """
        =={{int:filedesc}}==
        {{Information}}

        =={{int:license-header}}==
        {{Cc-by-2.0}}
    """
    )

    assert actual == expected


def test_adds_categories_to_wikitext() -> None:
    photo = get_typed_fixture(
        "flickr_api/single_photo-4452100167.json", model=SinglePhoto
    )

    actual = create_wikitext(
        photo,
        wikimedia_username="TestUser",
        new_categories=["Pictures of fish", "Pictures of fish in England"],
    )

    expected = tidy(
        """
        =={{int:filedesc}}==
        {{Information}}

        =={{int:license-header}}==
        {{Cc-by-2.0}}

        [[Category:Pictures of fish]]
        [[Category:Pictures of fish in England]]
    """
    )

    assert actual == expected


config = create_config(data_directory=pathlib.Path("data"))


@pytest.mark.parametrize("license_id", config["ALLOWED_LICENSES"])
def test_can_create_wikitext_for_all_allowed_licenses(license_id: str) -> None:
    photo = get_typed_fixture(
        "flickr_api/single_photo-4452100167.json", model=SinglePhoto
    )
    photo["license"]["id"] = license_id

    create_wikitext(photo, wikimedia_username="TestUser", new_categories=[])
