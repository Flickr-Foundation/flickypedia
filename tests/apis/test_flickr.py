import datetime
import json

import pytest

from flickypedia.apis.flickr import FlickrApi, FlickrApiException, ResourceNotFound


class DatetimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        else:  # pragma: no cover
            pass


@pytest.mark.parametrize(
    ["method", "params"],
    [
        ("get_single_photo", {"photo_id": "12345678901234567890"}),
    ],
)
def test_methods_fail_if_not_found(flickr_api, method, params):
    with pytest.raises(ResourceNotFound):
        getattr(flickr_api, method)(**params)


def test_it_throws_if_bad_auth(vcr_cassette):
    api = FlickrApi(api_key="doesnotexist")

    with pytest.raises(FlickrApiException):
        api.get_single_photo(photo_id="12345678901234567890")


def test_get_licenses(flickr_api):
    assert flickr_api.get_licenses() == {
        "0": {"id": "in-copyright", "label": "All Rights Reserved", "url": None},
        "1": {
            "id": "cc-by-nc-sa-2.0",
            "label": "CC BY-NC-SA 2.0",
            "url": "https://creativecommons.org/licenses/by-nc-sa/2.0/",
        },
        "2": {
            "id": "cc-by-nc-2.0",
            "label": "CC BY-NC 2.0",
            "url": "https://creativecommons.org/licenses/by-nc/2.0/",
        },
        "3": {
            "id": "cc-by-nc-nd-2.0",
            "label": "CC BY-NC-ND 2.0",
            "url": "https://creativecommons.org/licenses/by-nc-nd/2.0/",
        },
        "4": {
            "id": "cc-by-2.0",
            "label": "CC BY 2.0",
            "url": "https://creativecommons.org/licenses/by/2.0/",
        },
        "5": {
            "id": "cc-by-sa-2.0",
            "label": "CC BY-SA 2.0",
            "url": "https://creativecommons.org/licenses/by-sa/2.0/",
        },
        "6": {
            "id": "cc-by-nd-2.0",
            "label": "CC BY-ND 2.0",
            "url": "https://creativecommons.org/licenses/by-nd/2.0/",
        },
        "7": {
            "id": "nkcr",
            "label": "No known copyright restrictions",
            "url": "https://www.flickr.com/commons/usage/",
        },
        "8": {
            "id": "usgov",
            "label": "United States Government Work",
            "url": "http://www.usa.gov/copyright.shtml",
        },
        "9": {
            "id": "cc0-1.0",
            "label": "CC0 1.0",
            "url": "https://creativecommons.org/publicdomain/zero/1.0/",
        },
        "10": {
            "id": "pdm",
            "label": "Public Domain Mark",
            "url": "https://creativecommons.org/publicdomain/mark/1.0/",
        },
    }


def test_lookup_license_code(flickr_api):
    assert flickr_api.lookup_license_code(license_code="0") == {
        "id": "in-copyright",
        "label": "All Rights Reserved",
        "url": None,
    }


class TestGetSinglePhoto:
    def test_can_get_single_photo(self, flickr_api):
        info = flickr_api.get_single_photo(photo_id="32812033543")

        assert json.loads(json.dumps(info, cls=DatetimeEncoder)) == json.load(
            open("tests/fixtures/flickr_api/32812033543.json")
        )

    def test_sets_username_to_none_if_empty(self, flickr_api):
        info = flickr_api.get_single_photo(photo_id="31073485032")

        assert info["owner"] == {
            "id": "35591378@N03",
            "username": "Obama White House Archived",
            "realname": None,
        }

    def test_sets_granularity_on_date_taken(self, flickr_api):
        info = flickr_api.get_single_photo(photo_id="5240741057")

        assert info["date_taken"] == {
            "value": datetime.datetime(1950, 1, 1, 0, 0, 0),
            "granularity": 6,
            "unknown": False,
        }

    def test_sets_date_unknown_on_date_taken(self, flickr_api):
        info = flickr_api.get_single_photo(photo_id="25868667441")

        assert info["date_taken"] == {
            "value": datetime.datetime(2016, 3, 21, 16, 15, 39),
            "granularity": 0,
            "unknown": True,
        }
