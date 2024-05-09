import datetime
import re
import typing

import bs4
from flask import Flask, render_template
from flickr_photos_api import (
    DateTaken,
    LocationInfo,
    User as FlickrUser,
)
import pytest

from flickypedia.apis.structured_data import (
    create_copyright_status_statement,
    create_date_taken_statement,
    create_flickr_creator_statement,
    create_license_statement,
    create_location_statement,
    create_posted_to_flickr_statement,
    create_source_statement,
)
from flickypedia.types.structured_data import NewStatement


def prettify_html(html: str, find_kwargs: dict[str, typing.Any] | None = None) -> str:
    soup = bs4.BeautifulSoup(html, features="html.parser")

    if find_kwargs:
        soup = soup.find(**find_kwargs)  # type: ignore

    return soup.prettify(formatter="html")


def get_html(claims: list[NewStatement]) -> str:
    html = render_template(
        "prepare_info/structured_data_preview.html", structured_data={"claims": claims}
    )

    html = re.sub(r"\s+", " ", html)

    return prettify_html(
        html, find_kwargs={"name": "dl", "attrs": {"class": "structured_data_preview"}}
    )


@pytest.mark.parametrize(
    ["user", "html"],
    [
        pytest.param(
            {
                "id": "199246608@N02",
                "username": "Alex Chan",
                "realname": None,
                "path_alias": None,
                "photos_url": "https://www.flickr.com/photos/199246608@N02/",
                "profile_url": "https://www.flickr.com/people/199246608@N02/",
            },
            """
            <dt>creator:</dt>
            <dd class="snak-somevalue">
              <ul class="sdc_qualifiers plain_list">
                <li>
                  flickr user id: 199246608@N02
                </li>
                <li>
                  author name: Alex Chan
                </li>
                <li>
                  url: https://www.flickr.com/people/199246608@N02/
                </li>
              </ul>
            </dd>
            """,
            id="user_who_has_realname",
        ),
        pytest.param(
            {
                "id": "35591378@N03",
                "username": "Obama White House Archived",
                "realname": None,
                "path_alias": "obamawhitehouse",
                "photos_url": "https://www.flickr.com/photos/obamawhitehouse/",
                "profile_url": "https://www.flickr.com/people/obamawhitehouse/",
            },
            """
            <dt>creator:</dt>
            <dd class="snak-somevalue">
              <ul class="sdc_qualifiers plain_list">
                <li>
                  flickr user id: 35591378@N03
                </li>
                <li>
                  author name: Obama White House Archived
                </li>
                <li>
                  url: https://www.flickr.com/people/obamawhitehouse/
                </li>
              </ul>
            </dd>
            """,
            id="user_who_has_no_realname",
        ),
    ],
)
def test_shows_creator(app: Flask, user: FlickrUser, html: str) -> None:
    creator_claim = create_flickr_creator_statement(user=user)

    actual = get_html(claims=[creator_claim])

    expected = prettify_html(f'<dl class="structured_data_preview">{html}</dl>')

    assert actual == expected


def test_shows_copyright_status(app: Flask, vcr_cassette: str) -> None:
    copyright_claim = create_copyright_status_statement(license_id="cc-by-2.0")

    actual = get_html(claims=[copyright_claim])

    expected = prettify_html(
        """
        <dl class="structured_data_preview">
          <dt>copyright status:</dt>
          <dd class="snak-value">
            copyrighted
          </dd>
        </dl>
        """
    )

    assert actual == expected


def test_shows_source_data(app: Flask, vcr_cassette: str) -> None:
    source_claim = create_source_statement(
        photo_id="53248015596",
        photo_url="https://www.flickr.com/photos/199246608@N02/53248015596/",
        original_url="https://live.staticflickr.com/65535/53248015596_c03f8123cf_o_d.jpg",
        retrieved_at=datetime.datetime(2023, 11, 14, 16, 14, 0),
    )

    actual = get_html(claims=[source_claim])

    expected = prettify_html(
        """
        <dl class="structured_data_preview">
          <dt>source of file:</dt>
          <dd class="snak-value">
            file available on the internet
            <ul class="sdc_qualifiers plain_list">
              <li>
                described at url: https://www.flickr.com/photos/199246608@N02/53248015596/
              </li>
              <li>
                operator: Flickr
              </li>
              <li>
                url: https://live.staticflickr.com/65535/53248015596_c03f8123cf_o_d.jpg
              </li>
              <li>
                retrieved: 14 November 2023
              </li>
            </ul>
          </dd>
        </dl>
        """
    )

    assert actual == expected


def test_shows_license_statement(app: Flask, vcr_cassette: str) -> None:
    license_claim = create_license_statement(license_id="cc-by-2.0")

    actual = get_html(claims=[license_claim])

    expected = prettify_html(
        """
        <dl class="structured_data_preview">
          <dt>copyright license:</dt>
          <dd class="snak-value">
            Creative Commons Attribution 2.0 Generic
          </dd>
        </dl>
        """
    )

    assert actual == expected


def test_shows_posted_statement(app: Flask, vcr_cassette: str) -> None:
    posted_date_claim = create_posted_to_flickr_statement(
        date_posted=datetime.datetime(2023, 10, 12)
    )

    actual = get_html(claims=[posted_date_claim])

    expected = prettify_html(
        """
        <dl class="structured_data_preview">
          <dt>published in:</dt>
          <dd class="snak-value">
            Flickr
            <ul class="sdc_qualifiers plain_list">
              <li>
                publication date: 12 October 2023
              </li>
            </ul>
          </dd>
        </dl>
        """
    )

    assert actual == expected


@pytest.mark.parametrize(
    ["location", "expected_value"],
    [
        pytest.param(
            {"latitude": 49.968063, "longitude": 7.845047, "accuracy": 16},
            "49.968063&deg;N, 7.845047&deg;E",
            id="north_east",
        ),
        pytest.param(
            {"latitude": 40.696168, "longitude": -74.019446, "accuracy": 16},
            "40.696168&deg;N, 74.019446&deg;W",
            id="north_west",
        ),
        pytest.param(
            {"latitude": -12.507242, "longitude": 130.992966, "accuracy": 16},
            "12.507242&deg;S, 130.992966&deg;E",
            id="south_east",
        ),
        pytest.param(
            {"latitude": -25.683322, "longitude": -54.454829, "accuracy": 16},
            "25.683322&deg;S, 54.454829&deg;W",
            id="south_west",
        ),
    ],
)
def test_shows_location_statement(
    app: Flask, vcr_cassette: str, location: LocationInfo, expected_value: str
) -> None:
    actual = get_html(claims=[create_location_statement(location=location)])

    expected = prettify_html(
        f"""
        <dl class="structured_data_preview">
          <dt>location:</dt>
          <dd class="snak-value">
            {expected_value}
          </dd>
        </dl>
        """
    )

    assert actual == expected


@pytest.mark.parametrize(
    ["date_taken", "inception"],
    [
        pytest.param(
            {
                "value": datetime.datetime(2023, 10, 12),
                "granularity": "second",
                "unknown": False,
            },
            "12 October 2023",
            id="day_precision",
        ),
        pytest.param(
            {
                "value": datetime.datetime(2023, 10, 1),
                "granularity": "second",
                "unknown": False,
            },
            "1 October 2023",
            id="day_precision_with_single_digit_day",
        ),
        pytest.param(
            {
                "value": datetime.datetime(2023, 10, 12),
                "granularity": "month",
                "unknown": False,
            },
            "October 2023",
            id="month_precision",
        ),
        pytest.param(
            {
                "value": datetime.datetime(2023, 10, 12),
                "granularity": "year",
                "unknown": False,
            },
            "2023",
            id="year_precision",
        ),
        pytest.param(
            {
                "value": datetime.datetime(2023, 10, 12),
                "granularity": "circa",
                "unknown": False,
            },
            """
            2023
            <ul class="sdc_qualifiers plain_list">
              <li>
                sourcing circumstances: circa
              </li>
            </ul>
            """,
            id="circa_precision",
        ),
    ],
)
def test_shows_date_taken_statement_in_html(
    app: Flask, vcr_cassette: str, date_taken: DateTaken, inception: str
) -> None:
    date_taken_claim = create_date_taken_statement(date_taken=date_taken)

    actual = get_html(claims=[date_taken_claim])

    expected = prettify_html(
        f"""
        <dl class="structured_data_preview">
          <dt>date created:</dt>
          <dd class="snak-value">
            {inception}
          </dd>
        </dl>
        """
    )

    assert actual == expected
