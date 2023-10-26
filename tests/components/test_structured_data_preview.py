import re

import bs4
from flask import render_template
import pytest

from flickypedia.apis.structured_data import create_flickr_creator_statement


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
