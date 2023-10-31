import datetime
import json
import os

import pytest

from flickypedia.apis.flickr import FlickrApi, FlickrApiException, ResourceNotFound


def get_fixture(filename):
    with open(os.path.join("tests/fixtures/flickr_api", filename)) as f:
        return json.load(f)


def jsonify(v):
    """
    Cast a value to/from JSON, suitable for comparison with a JSON fixture.

    The reason we can't just compare directly, e.g.

        assert v == json.load(open("fixture.json"))

    is because some of our objects include ``datetime.datetime`` values,
    which are serialised as strings in the JSON.

    To enable easy comparisons, we need to turn the ``datetime.datetime``
    into strings.  e.g.

        >>> v = {'time': datetime.datetime.now()}
        >>> jsonify(v)
        {'time': '2023-10-20T13:30:45.567888'}

    You still get back a Python object, but now it can be compared to
    a value deserialised from JSON.

    """

    class DatetimeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            else:  # pragma: no cover
                pass

    return json.loads(json.dumps(v, cls=DatetimeEncoder))


@pytest.mark.parametrize(
    ["method", "params"],
    [
        ("get_single_photo", {"photo_id": "12345678901234567890"}),
        (
            "lookup_user",
            {"user_url": "https://www.flickr.com/photos/DefinitelyDoesNotExist"},
        ),
        # We have two variants of this test:
        #
        #   1. The user doesn't exist, so they can't possibly have any albums!
        #   2. The user exists, but the album ID doesn't
        #
        (
            "get_photos_in_album",
            {
                "user_url": "https://www.flickr.com/photos/DefinitelyDoesNotExist",
                "album_id": "1234",
            },
        ),
        (
            "get_photos_in_album",
            {
                "user_url": "https://www.flickr.com/photos/britishlibrary/",
                "album_id": "12345678901234567890",
            },
        ),
    ],
)
def test_methods_fail_if_not_found(flickr_api, method, params):
    with pytest.raises(ResourceNotFound):
        getattr(flickr_api, method)(**params)


def test_it_throws_if_bad_auth(vcr_cassette, user_agent):
    api = FlickrApi(api_key="doesnotexist", user_agent=user_agent)

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


@pytest.mark.parametrize(
    ["user_url", "user"],
    [
        (
            "https://www.flickr.com/photos/35591378@N03",
            {
                "id": "35591378@N03",
                "username": "Obama White House Archived",
                "realname": None,
                "photos_url": "https://www.flickr.com/photos/obamawhitehouse/",
                "profile_url": "https://www.flickr.com/people/obamawhitehouse/",
            },
        ),
        (
            "https://www.flickr.com/photos/britishlibrary/",
            {
                "id": "12403504@N02",
                "username": "The British Library",
                "realname": "British Library",
                "photos_url": "https://www.flickr.com/photos/britishlibrary/",
                "profile_url": "https://www.flickr.com/people/britishlibrary/",
            },
        ),
        (
            "https://www.flickr.com/photos/199246608@N02",
            {
                "id": "199246608@N02",
                "username": "cefarrjf87",
                "realname": "Alex Chan",
                "photos_url": "https://www.flickr.com/photos/199246608@N02/",
                "profile_url": "https://www.flickr.com/people/199246608@N02/",
            },
        ),
    ],
)
def test_lookup_user(flickr_api, user_url, user):
    assert flickr_api.lookup_user(user_url=user_url) == user


class TestGetSinglePhoto:
    def test_can_get_single_photo(self, flickr_api):
        resp = flickr_api.get_single_photo(photo_id="32812033543")

        assert jsonify(resp) == get_fixture(filename="32812033543.json")

    def test_sets_realname_to_none_if_empty(self, flickr_api):
        info = flickr_api.get_single_photo(photo_id="31073485032")

        assert info["owner"]["realname"] is None

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

    def test_empty_photo_description_is_none(self, flickr_api):
        photo_without_desc = flickr_api.get_single_photo(photo_id="5536044022")
        assert photo_without_desc["description"] is None

        photo_with_desc = flickr_api.get_single_photo(photo_id="53248070597")
        assert photo_with_desc["description"] == "Paris Montmartre"

    def test_empty_photo_title_is_none(self, flickr_api):
        photo_without_title = flickr_api.get_single_photo(photo_id="20967567081")
        assert photo_without_title["title"] is None

        photo_with_title = flickr_api.get_single_photo(photo_id="20428374183")
        assert photo_with_title["title"] == "Hapjeong"

    @pytest.mark.parametrize(
        ["photo_id", "original_format"],
        [
            ("53248070597", None),
            ("32812033543", "jpg"),
            ("12533665685", "png"),
            ("4079570071", "gif"),
        ],
    )
    def test_gets_original_format(self, flickr_api, photo_id, original_format):
        photo = flickr_api.get_single_photo(photo_id=photo_id)
        assert photo["original_format"] == original_format


class TestGetAlbum:
    def test_can_get_album(self, flickr_api):
        resp = flickr_api.get_photos_in_album(
            user_url="https://www.flickr.com/photos/spike_yun/",
            album_id="72157677773252346",
        )

        assert jsonify(resp) == get_fixture(filename="album-72157677773252346.json")

    def test_sets_owner_and_url_on_album_photos(self, flickr_api):
        resp = flickr_api.get_photos_in_album(
            user_url="https://www.flickr.com/photos/joshuatreenp/",
            album_id="72157640898611483",
        )

        assert resp["photos"][0]["owner"] == {
            "id": "115357548@N08",
            "username": "Joshua Tree National Park",
            "realname": None,
            "photos_url": "https://www.flickr.com/photos/joshuatreenp/",
            "profile_url": "https://www.flickr.com/people/joshuatreenp/",
        }

        assert (
            resp["photos"][0]["url"]
            == "https://www.flickr.com/photos/joshuatreenp/49021434741/"
        )

    def test_sets_date_unknown_on_date_taken_in_album(self, flickr_api):
        resp = flickr_api.get_photos_in_album(
            user_url="https://www.flickr.com/photos/nationalarchives/",
            album_id="72157664284840282",
        )

        assert resp["photos"][0]["date_taken"] == {
            "value": datetime.datetime(2016, 2, 9, 10, 1, 59),
            "granularity": 0,
            "unknown": True,
        }

    def test_only_gets_publicly_available_sizes(self, flickr_api):
        # This user doesn't allow downloading of their original photos,
        # so when we try to look up an album of their photos in the API,
        # we shouldn't get an Original size.
        resp = flickr_api.get_photos_in_album(
            user_url="https://www.flickr.com/photos/mary_faith/",
            album_id="72157711742505183",
        )

        assert not any(
            size for size in resp["photos"][0]["sizes"] if size["label"] == "Original"
        )

    def test_empty_album_title_is_none(self, flickr_api):
        album = flickr_api.get_photos_in_album(
            user_url="https://www.flickr.com/photos/spike_yun/",
            album_id="72157677773252346",
        )

        assert album["photos"][0]["title"] == "Seoul"
        assert album["photos"][7]["title"] is None

    def test_empty_album_description_is_none(self, flickr_api):
        album_without_desc = flickr_api.get_photos_in_album(
            user_url="https://www.flickr.com/photos/aljazeeraenglish/",
            album_id="72157626164453131",
        )

        assert all(
            photo["description"] is None for photo in album_without_desc["photos"]
        )

        album_with_desc = flickr_api.get_photos_in_album(
            user_url="https://www.flickr.com/photos/zeeyolqpictures/",
            album_id="72157631707062493",
        )

        assert all(
            isinstance(photo["description"], str) for photo in album_with_desc["photos"]
        )


@pytest.mark.parametrize(
    ["method", "kwargs"],
    [
        (
            "get_photos_in_album",
            {
                "user_url": "https://www.flickr.com/photos/spike_yun/",
                "album_id": "72157677773252346",
            },
        )
    ],
)
def test_get_collection_methods_are_paginated(flickr_api, method, kwargs):
    api_method = getattr(flickr_api, method)

    all_resp = api_method(**kwargs, page=1)

    # Getting the 5th page with a page size of 1 means getting the 5th image
    individual_resp = api_method(
        **kwargs,
        page=5,
        per_page=1,
    )

    assert individual_resp["photos"][0] == all_resp["photos"][4]
