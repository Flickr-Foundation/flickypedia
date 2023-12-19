import datetime
import pathlib
import textwrap

from flickr_photos_api import SinglePhoto
import pytest

from flickypedia.apis.wikitext import create_wikitext
from flickypedia.uploadr.config import create_config
from utils import get_typed_fixture


def tidy(s: str) -> str:
    return textwrap.dedent(s).strip()


def today() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d")


def test_create_wikitext_for_photo() -> None:
    photo = get_typed_fixture("flickr_photos_api/32812033543.json", model=SinglePhoto)
    photo["license"]["id"] = "cc-by-2.0"

    actual = create_wikitext(photo, wikimedia_username="TestUser", new_categories=[])
    expected = tidy(
        """
        =={{int:filedesc}}==
        {{Information
        |other fields=
        {{Flickr Tags 2|mascot|chiefbert|germanshepherd|stationelizabethcity|weekinthelife2017|ninabowen|d5|midatlantic|northcarolina|elizabethcity|explosivedetectiondog|unitedstates|us}}
        }}

        =={{int:license-header}}==
        {{Cc-by-2.0}}

        {{Uploaded with Flickypedia
        |user=TestUser
        |date=%s
        |flickrUser=U.S. Coast Guard
        |flickrUserUrl=https://www.flickr.com/people/coast_guard/
        |flickrPhotoUrl=https://www.flickr.com/photos/coast_guard/32812033543/
        }}
    """
        % today()
    )

    assert actual == expected


def test_adds_categories_to_wikitext() -> None:
    photo = get_typed_fixture("flickr_photos_api/32812033543.json", model=SinglePhoto)

    actual = create_wikitext(
        photo,
        wikimedia_username="TestUser",
        new_categories=["Pictures of fish", "Pictures of fish in England"],
    )

    expected = tidy(
        """
        =={{int:filedesc}}==
        {{Information
        |other fields=
        {{Flickr Tags 2|mascot|chiefbert|germanshepherd|stationelizabethcity|weekinthelife2017|ninabowen|d5|midatlantic|northcarolina|elizabethcity|explosivedetectiondog|unitedstates|us}}
        }}

        =={{int:license-header}}==
        {{PD-USGov}}

        {{Uploaded with Flickypedia
        |user=TestUser
        |date=%s
        |flickrUser=U.S. Coast Guard
        |flickrUserUrl=https://www.flickr.com/people/coast_guard/
        |flickrPhotoUrl=https://www.flickr.com/photos/coast_guard/32812033543/
        }}

        [[Category:Pictures of fish]]
        [[Category:Pictures of fish in England]]
    """
        % today()
    )

    assert actual == expected


def test_adds_location_to_wikitext() -> None:
    photo = get_typed_fixture("flickr_photos_api/32812033543.json", model=SinglePhoto)
    photo["tags"] = []
    photo["location"] = {"latitude": 50.0, "longitude": 50.0, "accuracy": 16}

    wikitext = create_wikitext(
        photo,
        wikimedia_username="TestUser",
        new_categories=[],
    )

    assert "{{Information}}\n{{Location}}\n" in wikitext


def test_it_skips_tags_if_none_on_photo() -> None:
    photo = get_typed_fixture("flickr_photos_api/32812033543.json", model=SinglePhoto)
    photo["tags"] = []

    wikitext = create_wikitext(
        photo,
        wikimedia_username="TestUser",
        new_categories=[],
    )

    assert "Flickr Tags 2" not in wikitext
    assert "{{Information}}" in wikitext


config = create_config(data_directory=pathlib.Path("data"))


@pytest.mark.parametrize("license_id", config["ALLOWED_LICENSES"])
def test_can_create_wikitext_for_all_allowed_licenses(license_id: str) -> None:
    photo = get_typed_fixture("flickr_photos_api/32812033543.json", model=SinglePhoto)
    photo["license"]["id"] = license_id

    create_wikitext(photo, wikimedia_username="TestUser", new_categories=[])
