import datetime
import re

import bs4
from flask import render_template
import pytest

from flickypedia.apis.structured_data import (
    create_copyright_status_statement,
    create_date_taken_statement,
    create_flickr_creator_statement,
    create_license_statement,
    create_posted_to_flickr_statement,
    create_source_data_for_photo,
)


def prettify_html(html, find_kwargs=None):
    soup = bs4.BeautifulSoup(html, features="html.parser")

    if find_kwargs:
        soup = soup.find(**find_kwargs)

    return soup.prettify(formatter="html")


def get_html(claims):
    html = render_template(
        "components/structured_data_preview.html", structured_data=claims
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
                "id": "47397743@N05",
                "username": None,
                "realname": "WNDC",
                "photos_url": "https://www.flickr.com/photos/west_northamptonshire_development_corporation/",
                "profile_url": "https://www.flickr.com/people/west_northamptonshire_development_corporation/",
            },
            """
            <dt>creator:</dt>
            <dd class="snak-value">
              West Northamptonshire Development Corporation (Q7986087)
            </dd>
            """,
            id="user_who_is_wikidata_entity",
        ),
        pytest.param(
            {
                "id": "199246608@N02",
                "username": "Alex Chan",
                "realname": None,
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
            id="user_who_is_not_wikidata_entity",
        ),
        pytest.param(
            {
                "id": "35591378@N03",
                "username": "Obama White House Archived",
                "realname": None,
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
def test_shows_creator(app, vcr_cassette, user, html):
    creator_claim = create_flickr_creator_statement(user=user)

    actual = get_html(claims=[creator_claim])

    expected = prettify_html(f'<dl class="structured_data_preview">{html}</dl>')

    assert actual == expected


def test_shows_copyright_status(app, vcr_cassette):
    copyright_claim = create_copyright_status_statement(status="copyrighted")

    actual = get_html(claims=[copyright_claim])

    expected = prettify_html(
        """
        <dl class="structured_data_preview">
          <dt>copyright status:</dt>
          <dd class="snak-value">
            copyrighted (Q50423863)
          </dd>
        </dl>
        """
    )

    assert actual == expected


def test_shows_source_data(app, vcr_cassette):
    source_claim = create_source_data_for_photo(
        photo_url="https://www.flickr.com/photos/199246608@N02/53248015596/",
        original_url="https://live.staticflickr.com/65535/53248015596_c03f8123cf_o_d.jpg",
    )

    actual = get_html(claims=[source_claim])

    expected = prettify_html(
        """
        <dl class="structured_data_preview">
          <dt>source of file:</dt>
          <dd class="snak-value">
            file available on the internet (Q74228490)
            <ul class="sdc_qualifiers plain_list">
              <li>
                described at url: https://www.flickr.com/photos/199246608@N02/53248015596/
              </li>
              <li>
                operator: Flickr (Q103204)
              </li>
              <li>
                url: https://live.staticflickr.com/65535/53248015596_c03f8123cf_o_d.jpg
              </li>
            </ul>
          </dd>
        </dl>
        """
    )

    assert actual == expected


def test_shows_license_statement(app, vcr_cassette):
    license_claim = create_license_statement(license_id="cc-by-2.0")

    actual = get_html(claims=[license_claim])

    expected = prettify_html(
        """
        <dl class="structured_data_preview">
          <dt>copyright license:</dt>
          <dd class="snak-value">
            Creative Commons Attribution 2.0 Generic (Q19125117)
          </dd>
        </dl>
        """
    )

    assert actual == expected


def test_shows_posted_statement(app, vcr_cassette):
    posted_date_claim = create_posted_to_flickr_statement(
        date_posted=datetime.datetime(2023, 10, 12)
    )

    actual = get_html(claims=[posted_date_claim])

    expected = prettify_html(
        """
        <dl class="structured_data_preview">
          <dt>published in:</dt>
          <dd class="snak-value">
            Flickr (Q103204)
            <ul class="sdc_qualifiers plain_list">
              <li>
                publication date: 12 October 2023 (precision: day, calendar: Gregorian)
              </li>
            </ul>
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
                "granularity": 0,
            },
            "12 October 2023 (precision: day, calendar: Gregorian)",
            id="day_precision",
        ),
        pytest.param(
            {
                "value": datetime.datetime(2023, 10, 1),
                "granularity": 0,
            },
            "1 October 2023 (precision: day, calendar: Gregorian)",
            id="day_precision_with_single_digit_day",
        ),
        pytest.param(
            {
                "value": datetime.datetime(2023, 10, 12),
                "granularity": 4,
            },
            "October 2023 (precision: month, calendar: Gregorian)",
            id="month_precision",
        ),
        pytest.param(
            {
                "value": datetime.datetime(2023, 10, 12),
                "granularity": 6,
            },
            "2023 (precision: year, calendar: Gregorian)",
            id="year_precision",
        ),
        pytest.param(
            {
                "value": datetime.datetime(2023, 10, 12),
                "granularity": 8,
            },
            """
            2023 (precision: year, calendar: Gregorian)
            <ul class="sdc_qualifiers plain_list">
              <li>
                sourcing circumstances: circa (Q5727902)
              </li>
            </ul>
            """,
            id="circa_precision",
        ),
    ],
)
def test_shows_date_taken_statement_in_html(app, vcr_cassette, date_taken, inception):
    date_taken_claim = create_date_taken_statement(
        date_taken={**date_taken, "unknown": False}
    )

    actual = get_html(claims=[date_taken_claim])

    expected = prettify_html(
        f"""
        <dl class="structured_data_preview">
          <dt>inception:</dt>
          <dd class="snak-value">
            {inception}
          </dd>
        </dl>
        """
    )

    assert actual == expected
