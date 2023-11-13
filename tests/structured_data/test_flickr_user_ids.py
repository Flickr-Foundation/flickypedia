from flickr_photos_api import User as FlickrUser

from flickr_sdc.flickr_user_ids import lookup_flickr_user_in_wikidata


def test_can_find_user_by_user_id(vcr_cassette: str) -> None:
    user: FlickrUser = {
        "id": "57928590@N07",
        "username": "Das Saarland",
        "realname": None,
        "path_alias": "saarland_de",
        "photos_url": "https://www.flickr.com/photos/saarland_de/",
        "profile_url": "https://www.flickr.com/people/saarland_de/",
    }

    assert lookup_flickr_user_in_wikidata(user) == "Q1201"


def test_can_find_user_by_path_alias(vcr_cassette: str) -> None:
    user: FlickrUser = {
        "id": "38153300@N00",
        "username": "elfsternberg",
        "realname": "Elf Sternberg",
        "path_alias": "elfsternberg",
        "photos_url": "https://www.flickr.com/photos/elfsternberg/",
        "profile_url": "https://www.flickr.com/people/elfsternberg/",
    }

    assert lookup_flickr_user_in_wikidata(user) == "Q5359860"


def test_returns_none_if_it_cannot_find_user(vcr_cassette: str) -> None:
    user: FlickrUser = {
        "id": "23594237@N02",
        "username": "MAMJODH",
        "realname": None,
        "path_alias": "mahjodh",
        "photos_url": "https://www.flickr.com/photos/mahjodh/",
        "profile_url": "https://www.flickr.com/people/mahjodh/",
    }

    assert lookup_flickr_user_in_wikidata(user) is None


def test_returns_none_if_it_cannot_find_user_with_only_id(vcr_cassette: str) -> None:
    user: FlickrUser = {
        "id": "196253572@N05",
        "photos_url": "https://www.flickr.com/photos/196253572@N05/",
        "profile_url": "https://www.flickr.com/people/196253572@N05/",
        "realname": "Raymond Wiggers",
        "username": "rwgabbro1",
        "path_alias": None,
    }

    assert lookup_flickr_user_in_wikidata(user) is None
