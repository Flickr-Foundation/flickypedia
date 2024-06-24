from flickr_photos_api import User as FlickrUser
import pytest

from flickypedia.structured_data.statements import create_flickr_creator_statement
from utils import get_statement_fixture


@pytest.mark.parametrize(
    ["user", "filename"],
    [
        (
            {
                "id": "47397743@N05",
                "username": None,
                "realname": "WNDC",
                "path_alias": "west_northamptonshire_development_corporation",
                "photos_url": "https://www.flickr.com/photos/west_northamptonshire_development_corporation/",
                "profile_url": "https://www.flickr.com/people/west_northamptonshire_development_corporation/",
            },
            "creator_WNDC.json",
        ),
        (
            {
                "id": "199246608@N02",
                "username": "Alex Chan",
                "realname": None,
                "path_alias": None,
                "photos_url": "https://www.flickr.com/photos/199246608@N02/",
                "profile_url": "https://www.flickr.com/people/199246608@N02/",
            },
            "creator_AlexChan.json",
        ),
        (
            {
                "id": "35591378@N03",
                "username": "Obama White House Archived",
                "realname": None,
                "path_alias": "obamawhitehouse",
                "photos_url": "https://www.flickr.com/photos/obamawhitehouse/",
                "profile_url": "https://www.flickr.com/people/obamawhitehouse/",
            },
            "creator_ObamaWhiteHouse.json",
        ),
    ],
)
def test_create_creator_statement(user: FlickrUser, filename: str) -> None:
    result = create_flickr_creator_statement(user)
    expected = get_statement_fixture(filename)

    assert result == expected
