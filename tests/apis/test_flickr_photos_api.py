import datetime

import pytest

from flickypedia.apis.flickr import (
    FlickrPhotosApi,
    FlickrApiException,
    LicenseNotFound,
    ResourceNotFound,
)
from flickypedia.apis.flickr.utils import (
    parse_date_taken_granularity,
    parse_safety_level,
)
from flickypedia.types.flickr import (
    User,
    SinglePhoto,
    CollectionOfPhotos,
    PhotosInAlbum,
    PhotosInGallery,
    PhotosInGroup,
)
from utils import get_typed_fixture


@pytest.mark.parametrize(
    ["method", "params"],
    [
        pytest.param(
            "lookup_user_by_url",
            {"url": "https://www.flickr.com/photos/DefinitelyDoesNotExist"},
            id="lookup_user_by_url",
        ),
        pytest.param(
            "get_single_photo",
            {"photo_id": "12345678901234567890"},
            id="get_single_photo",
        ),
        pytest.param(
            "get_photos_in_album",
            {
                "user_url": "https://www.flickr.com/photos/DefinitelyDoesNotExist",
                "album_id": "1234",
            },
            id="get_photos_in_album_with_missing_user",
        ),
        pytest.param(
            "get_photos_in_album",
            {
                "user_url": "https://www.flickr.com/photos/britishlibrary/",
                "album_id": "12345678901234567890",
            },
            id="get_photos_in_album_with_missing_album",
        ),
        pytest.param(
            "get_photos_in_gallery",
            {"gallery_id": "12345678901234567890"},
            id="get_photos_in_gallery",
        ),
        pytest.param(
            "get_public_photos_by_user",
            {"user_url": "https://www.flickr.com/photos/DefinitelyDoesNotExist"},
            id="get_public_photos_by_non_existent_user",
        ),
        pytest.param(
            "get_photos_in_group_pool",
            {"group_url": "https://www.flickr.com/groups/doesnotexist/pool/"},
            id="get_photos_in_non_existent_group_pool",
        ),
    ],
)
def test_methods_fail_if_not_found(
    flickr_api: FlickrPhotosApi, method: str, params: dict[str, str]
) -> None:
    api_method = getattr(flickr_api, method)

    with pytest.raises(ResourceNotFound):
        api_method(**params)


def test_it_throws_if_bad_auth(vcr_cassette: str, user_agent: str) -> None:
    flickr_api = FlickrPhotosApi(api_key="doesnotexist", user_agent=user_agent)

    with pytest.raises(FlickrApiException):
        flickr_api.lookup_user_by_url(url="https://www.flickr.com/photos/flickr/")


class TestLicenses:
    def test_get_licenses(self, flickr_api: FlickrPhotosApi) -> None:
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

    def test_lookup_license_by_id(self, flickr_api: FlickrPhotosApi) -> None:
        assert flickr_api.lookup_license_by_id(id="0") == {
            "id": "in-copyright",
            "label": "All Rights Reserved",
            "url": None,
        }

    def test_throws_license_not_found_for_bad_id(
        self, flickr_api: FlickrPhotosApi
    ) -> None:
        with pytest.raises(LicenseNotFound, match="ID -1"):
            flickr_api.lookup_license_by_id(id="-1")


@pytest.mark.parametrize(
    ["url", "user"],
    [
        # A user who doesn't have a "realname" assigned
        pytest.param(
            "https://www.flickr.com/photos/35591378@N03",
            {
                "id": "35591378@N03",
                "username": "Obama White House Archived",
                "realname": None,
                "path_alias": "obamawhitehouse",
                "photos_url": "https://www.flickr.com/photos/obamawhitehouse/",
                "profile_url": "https://www.flickr.com/people/obamawhitehouse/",
            },
            id="obamawhitehouse",
        ),
        # A user who has a username, but their username is different from
        # their path alias.
        #
        # i.e. although the user URL ends 'britishlibrary', if you look up
        # the user with username 'britishlibrary' you'll find somebody different.
        pytest.param(
            "https://www.flickr.com/photos/britishlibrary/",
            {
                "id": "12403504@N02",
                "username": "The British Library",
                "realname": "British Library",
                "path_alias": "britishlibrary",
                "photos_url": "https://www.flickr.com/photos/britishlibrary/",
                "profile_url": "https://www.flickr.com/people/britishlibrary/",
            },
            id="britishlibrary",
        ),
        # A user URL that uses the numeric ID rather than a path alias.
        pytest.param(
            "https://www.flickr.com/photos/199246608@N02",
            {
                "id": "199246608@N02",
                "username": "cefarrjf87",
                "realname": "Alex Chan",
                "path_alias": None,
                "photos_url": "https://www.flickr.com/photos/199246608@N02/",
                "profile_url": "https://www.flickr.com/people/199246608@N02/",
            },
            id="199246608@N02",
        ),
    ],
)
def test_lookup_user_by_url(flickr_api: FlickrPhotosApi, url: str, user: User) -> None:
    assert flickr_api.lookup_user_by_url(url=url) == user


class TestGetSinglePhoto:
    def test_can_get_single_photo(self, flickr_api: FlickrPhotosApi) -> None:
        actual = flickr_api.get_single_photo(photo_id="32812033543")

        expected = get_typed_fixture(
            "flickr_photos_api/32812033543.json", model=SinglePhoto
        )

        assert actual == expected

    def test_sets_realname_to_none_if_empty(self, flickr_api: FlickrPhotosApi) -> None:
        info = flickr_api.get_single_photo(photo_id="31073485032")

        assert info["owner"]["realname"] is None

    def test_sets_granularity_on_date_taken(self, flickr_api: FlickrPhotosApi) -> None:
        info = flickr_api.get_single_photo(photo_id="5240741057")

        assert info["date_taken"] == {
            "value": datetime.datetime(1950, 1, 1, 0, 0, 0),
            "granularity": "year",
        }

    def test_sets_date_unknown_on_date_taken(self, flickr_api: FlickrPhotosApi) -> None:
        info = flickr_api.get_single_photo(photo_id="25868667441")

        assert info["date_taken"] is None

    def test_gets_photo_description(self, flickr_api: FlickrPhotosApi) -> None:
        photo = flickr_api.get_single_photo(photo_id="53248070597")
        assert photo["description"] == "Paris Montmartre"

    def test_empty_photo_description_is_none(self, flickr_api: FlickrPhotosApi) -> None:
        photo = flickr_api.get_single_photo(photo_id="5536044022")
        assert photo["description"] is None

    def test_gets_photo_title(self, flickr_api: FlickrPhotosApi) -> None:
        photo_with_title = flickr_api.get_single_photo(photo_id="20428374183")
        assert photo_with_title["title"] == "Hapjeong"

    def test_empty_photo_title_is_none(self, flickr_api: FlickrPhotosApi) -> None:
        photo_without_title = flickr_api.get_single_photo(photo_id="20967567081")
        assert photo_without_title["title"] is None

    @pytest.mark.parametrize(
        ["photo_id", "original_format"],
        [
            ("53248070597", None),
            ("32812033543", "jpg"),
            ("12533665685", "png"),
            ("4079570071", "gif"),
        ],
    )
    def test_gets_original_format(
        self, flickr_api: FlickrPhotosApi, photo_id: str, original_format: str
    ) -> None:
        photo = flickr_api.get_single_photo(photo_id=photo_id)
        assert photo["original_format"] == original_format

    def test_sets_human_readable_safety_level(
        self, flickr_api: FlickrPhotosApi
    ) -> None:
        photo = flickr_api.get_single_photo(photo_id="53248070597")
        assert photo["safety_level"] == "safe"

    def test_get_empty_tags_for_untagged_photo(
        self, flickr_api: FlickrPhotosApi
    ) -> None:
        photo = flickr_api.get_single_photo(photo_id="53331717974")
        assert photo["tags"] == []

    def test_gets_location_for_photo(self, flickr_api: FlickrPhotosApi) -> None:
        photo = flickr_api.get_single_photo(photo_id="52994452213")

        assert photo["location"] == {
            "latitude": 9.135158,
            "longitude": 40.083811,
            "accuracy": 16,
        }

    def test_get_empty_location_for_photo_without_geo(
        self, flickr_api: FlickrPhotosApi
    ) -> None:
        photo = flickr_api.get_single_photo(photo_id="53305573272")

        assert photo["location"] is None

    def test_it_discards_location_if_accuracy_is_zero(
        self, flickr_api: FlickrPhotosApi
    ) -> None:
        # This is an photo with some geo/location information, but the accuracy parameter is 0, which we treat as so low as to be unusable.
        photo = flickr_api.get_single_photo(photo_id="52578982111")

        assert photo["location"] is None


class TestCollectionsPhotoResponse:
    """
    This class contains tests for the _parse_collection_of_photos_response,
    which is shared among all collection responses (albums, galleries, etc.)

    We don't want to expose/test that function directly; instead we test
    how it affects the final response.
    """

    def test_sets_owner_and_url_on_collection(
        self, flickr_api: FlickrPhotosApi
    ) -> None:
        resp = flickr_api.get_photos_in_album(
            user_url="https://www.flickr.com/photos/joshuatreenp/",
            album_id="72157640898611483",
        )

        assert resp["photos"][0]["owner"] == {
            "id": "115357548@N08",
            "username": "Joshua Tree National Park",
            "realname": None,
            "path_alias": "joshuatreenp",
            "photos_url": "https://www.flickr.com/photos/joshuatreenp/",
            "profile_url": "https://www.flickr.com/people/joshuatreenp/",
        }

        assert (
            resp["photos"][0]["url"]
            == "https://www.flickr.com/photos/joshuatreenp/49021434741/"
        )

    def test_sets_date_unknown_on_date_taken_in_collection(
        self, flickr_api: FlickrPhotosApi
    ) -> None:
        resp = flickr_api.get_photos_in_album(
            user_url="https://www.flickr.com/photos/nationalarchives/",
            album_id="72157664284840282",
        )

        assert resp["photos"][0]["date_taken"] is None

    def test_only_gets_publicly_available_sizes(
        self, flickr_api: FlickrPhotosApi
    ) -> None:
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

    def test_sets_originalformat_to_none_if_no_downloads(
        self, flickr_api: FlickrPhotosApi
    ) -> None:
        # This user doesn't allow downloading of their original photos,
        # so when we try to look up an album of their photos in the API,
        # we shouldn't get an Original size.
        resp = flickr_api.get_photos_in_album(
            user_url="https://www.flickr.com/photos/mary_faith/",
            album_id="72157711742505183",
        )

        assert all(photo["original_format"] is None for photo in resp["photos"])

    def test_gets_location_on_collection_photos(
        self, flickr_api: FlickrPhotosApi
    ) -> None:
        resp = flickr_api.get_photos_in_album(
            user_url="https://www.flickr.com/photos/150102727@N06/",
            album_id="72157700908640782",
        )

        assert any(photo["location"] is None for photo in resp["photos"])

    def test_discards_location_if_accuracy_zero(
        self, flickr_api: FlickrPhotosApi
    ) -> None:
        # This is an album where every photo has some geo/location information,
        # but the accuracy parameter is 0, which we treat as such low accuracy
        # as to be unusable.
        resp = flickr_api.get_photos_in_album(
            user_url="https://www.flickr.com/photos/rudrpeter/",
            album_id="72157633859840285",
            per_page=1,
        )

        assert all(photo["location"] is None for photo in resp["photos"])


class TestGetAlbum:
    def test_can_get_album(self, flickr_api: FlickrPhotosApi) -> None:
        actual = flickr_api.get_photos_in_album(
            user_url="https://www.flickr.com/photos/spike_yun/",
            album_id="72157677773252346",
        )

        expected = get_typed_fixture(
            "flickr_photos_api/album-72157677773252346.json", model=PhotosInAlbum
        )

        assert actual == expected

    def test_empty_album_title_is_none(self, flickr_api: FlickrPhotosApi) -> None:
        album = flickr_api.get_photos_in_album(
            user_url="https://www.flickr.com/photos/spike_yun/",
            album_id="72157677773252346",
        )

        assert album["photos"][0]["title"] == "Seoul"
        assert album["photos"][7]["title"] is None

    def test_empty_album_description_is_none(self, flickr_api: FlickrPhotosApi) -> None:
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


def test_get_gallery_from_id(flickr_api: FlickrPhotosApi) -> None:
    actual = flickr_api.get_photos_in_gallery(gallery_id="72157720932863274")

    expected = get_typed_fixture(
        "flickr_photos_api/gallery-72157677773252346.json", model=PhotosInGallery
    )

    assert actual == expected


def test_get_public_photos_by_user(flickr_api: FlickrPhotosApi) -> None:
    actual = flickr_api.get_public_photos_by_user(
        user_url="https://www.flickr.com/photos/george"
    )

    expected = get_typed_fixture(
        "flickr_photos_api/user-george.json", model=CollectionOfPhotos
    )

    assert actual == expected


def test_get_photos_in_group_pool(flickr_api: FlickrPhotosApi) -> None:
    actual = flickr_api.get_photos_in_group_pool(
        group_url="https://www.flickr.com/groups/slovenia/pool/"
    )

    expected = get_typed_fixture(
        "flickr_photos_api/group-slovenia.json", model=PhotosInGroup
    )

    assert actual == expected


def test_get_photos_with_tag(flickr_api: FlickrPhotosApi) -> None:
    actual = flickr_api.get_photos_with_tag(tag="sunset")

    expected = get_typed_fixture(
        "flickr_photos_api/tag-sunset.json", model=CollectionOfPhotos
    )

    assert actual == expected


@pytest.mark.parametrize(
    ["method", "kwargs"],
    [
        pytest.param(
            "get_photos_in_album",
            {
                "user_url": "https://www.flickr.com/photos/spike_yun/",
                "album_id": "72157677773252346",
            },
            id="get_photos_in_album",
        ),
        pytest.param(
            "get_photos_in_gallery",
            {"gallery_id": "72157720932863274"},
            id="get_photos_in_gallery",
        ),
        pytest.param(
            "get_public_photos_by_user",
            {"user_url": "https://www.flickr.com/photos/george/"},
            id="get_public_photos_by_user",
        ),
        pytest.param(
            "get_photos_in_group_pool",
            {"group_url": "https://www.flickr.com/groups/slovenia/pool/"},
            id="get_photos_in_group_pool",
        ),
        pytest.param(
            "get_photos_with_tag", {"tag": "sunset"}, id="get_photos_with_tag"
        ),
    ],
)
def test_get_collection_methods_are_paginated(
    flickr_api: FlickrPhotosApi, method: str, kwargs: dict[str, str]
) -> None:
    api_method = getattr(flickr_api, method)

    all_resp = api_method(**kwargs, page=1)

    # Getting the 5th page with a page size of 1 means getting the 5th image
    individual_resp = api_method(
        **kwargs,
        page=5,
        per_page=1,
    )

    assert individual_resp["photos"][0] == all_resp["photos"][4]


def test_unrecognised_safety_level_is_error() -> None:
    with pytest.raises(ValueError, match="Unrecognised safety level"):
        parse_safety_level("-1")


def test_unrecognised_date_granularity_is_error() -> None:
    with pytest.raises(ValueError, match="Unrecognised date granularity"):
        parse_date_taken_granularity("-1")


@pytest.mark.parametrize(
    ["user_id", "expected_url"],
    [
        pytest.param(
            "199246608@N02",
            "https://www.flickr.com/images/buddyicon.gif",
            id="user_with_no_buddyicon",
        ),
        pytest.param(
            "28660070@N07",
            "https://farm6.staticflickr.com/5556/buddyicons/28660070@N07.jpg",
            id="user_with_buddyicon",
        ),
    ],
)
def test_get_buddy_icon_url(
    flickr_api: FlickrPhotosApi, user_id: str, expected_url: str
) -> None:
    assert flickr_api.get_buddy_icon_url(user_id=user_id) == expected_url
