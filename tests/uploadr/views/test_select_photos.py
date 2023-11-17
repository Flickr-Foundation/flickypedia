import bs4
from flask import Flask
from flask.testing import FlaskClient
from flickr_photos_api import FlickrPhotosApi
import pytest

from flickypedia.apis.flickr import PhotosInAlbumData, SinglePhotoData
from flickypedia.uploadr.views.select_photos import save_cached_photos_data
from utils import minify, get_typed_fixture


@pytest.mark.parametrize(
    "url",
    [
        "/select_photos",
        "/select_photos?flickr_url=no",
        "/select_photos?flickr_url=https://example.net",
    ],
)
def test_rejects_pages_with_bad_query_params(
    logged_in_client: FlaskClient, url: str
) -> None:
    resp = logged_in_client.get(url)

    assert resp.status_code == 400


def test_can_select_single_photo_on_flickr(
    logged_in_client: FlaskClient, flickr_api: FlickrPhotosApi
) -> None:
    resp = logged_in_client.get(
        "/select_photos?flickr_url=https://www.flickr.com/photos/199246608@N02/53253175319/"
    )

    assert resp.status_code == 302
    assert resp.headers["location"].startswith(
        "/prepare_info?selected_photo_ids=53253175319&cache_id="
    )


def test_duplicate_single_photo_on_flickr_is_not_allowed(
    logged_in_client: FlaskClient, flickr_api: FlickrPhotosApi
) -> None:
    resp = logged_in_client.get(
        "/select_photos?flickr_url=https://www.flickr.com/photos/fotnmc/9999819294/"
    )

    assert resp.status_code == 200
    assert b"Your work is done!" in resp.data


def test_single_photo_with_bad_license_is_not_allowed(
    logged_in_client: FlaskClient, flickr_api: FlickrPhotosApi
) -> None:
    resp = logged_in_client.get(
        "/select_photos?flickr_url=https://www.flickr.com/photos/ryanschude/50868060871/"
    )

    assert resp.status_code == 200
    assert "This photo can’t be used" in resp.data.decode("utf8")


@pytest.mark.parametrize(
    ["flickr_url", "description"],
    [
        pytest.param(
            "https://www.flickr.com/photos/aljazeeraenglish/albums/72157626164453131/",
            "You’re looking at Al Jazeera English’s album called “Faces from the Libyan front”.",
            id="album",
        ),
        pytest.param(
            "https://www.flickr.com/photos/george/",
            "You’re looking at photos taken by George Oates.",
            id="user",
        ),
        pytest.param(
            "https://www.flickr.com/photos/flickr/galleries/72157720348635494/",
            "You’re looking at Flickr’s gallery called “Popular Creative Commons Licensed Photos Shared in 2021”.",
            id="gallery",
        ),
        pytest.param(
            "https://www.flickr.com/groups/uruguay/",
            "You’re looking at photos from the Uruguay group.",
            id="group",
        ),
        pytest.param(
            "https://www.flickr.com/photos/tags/nature/",
            "You’re looking at photos tagged with nature.",
            id="tag",
        ),
    ],
)
def test_shows_correct_description(
    logged_in_client: FlaskClient,
    flickr_api: FlickrPhotosApi,
    flickr_url: str,
    description: str,
) -> None:
    resp = logged_in_client.get(f"/select_photos?flickr_url={flickr_url}")

    assert resp.status_code == 200

    soup = bs4.BeautifulSoup(minify(resp.data), "html.parser")

    description_elem = soup.find("h2", attrs={"class": "select_photos_description"})
    assert description_elem.getText().strip() == description  # type: ignore

    # Check there's at least one photo in the list.
    assert len(soup.find("ul", attrs={"class": "photoslist"}).find_all("li")) > 1  # type: ignore


def test_gets_album_on_flickr(
    logged_in_client: FlaskClient, flickr_api: FlickrPhotosApi
) -> None:
    resp = logged_in_client.get(
        "/select_photos?flickr_url=https://www.flickr.com/photos/aljazeeraenglish/albums/72157626164453131/"
    )

    assert resp.status_code == 200
    assert b"by Al Jazeera English" not in resp.data


@pytest.mark.parametrize(
    ["url", "error"],
    [
        pytest.param(
            "https://www.flickr.com/photos/doesnotexist/12345678901234567890",
            b"There is no photo at that URL!",
            id="single_photo",
        ),
        pytest.param(
            "https://www.flickr.com/photos/doesnotexist/albums/12345678901234567890/",
            b"There is no album at that URL!",
            id="album",
        ),
        pytest.param(
            "https://www.flickr.com/photos/thisuserdoesnotexist/",
            b"There is no user at that URL!",
            id="album",
        ),
        pytest.param(
            "https://www.flickr.com/photos/doesnotexist/galleries/12345678901234567890/",
            b"There is no gallery at that URL!",
            id="gallery",
        ),
        pytest.param(
            "https://www.flickr.com/groups/doesnotexist/",
            b"There is no group at that URL!",
            id="group",
        ),
        pytest.param(
            "https://www.flickr.com/photos/tags/ThereIsNothingInThisTag/",
            b"There are no photos with that tag!",
            id="tag",
        ),
    ],
)
def test_redirects_to_get_photos_if_resource_not_found(
    logged_in_client: FlaskClient, flickr_api: FlickrPhotosApi, url: str, error: bytes
) -> None:
    """
    If you try to look up a non-existent URL, you should be redirected
    back to the find photos screen, where:

    *   There's an error message about there being no URLs at this page
    *   Your URL is pre-filled in the input box

    """
    resp = logged_in_client.get(f"/select_photos?flickr_url={url}")
    assert resp.status_code == 302
    assert resp.headers["location"] == "/get_photos"

    redirected_resp = logged_in_client.get(resp.headers["location"])
    assert redirected_resp.status_code == 200

    assert error in redirected_resp.data
    assert f'value="{url}"'.encode("ascii") in redirected_resp.data


def test_no_photo_selection_is_error(
    logged_in_client: FlaskClient, flickr_api: FlickrPhotosApi
) -> None:
    """
    If you POST a form without a selection, you get an error.
    """
    flickr_url = "https://www.flickr.com/photos/schlesinger_library/13270291833/"

    resp = logged_in_client.post(f"/select_photos?flickr_url={flickr_url}")

    assert resp.status_code == 200
    assert b"You need to select at least one photo!" in resp.data


def test_selecting_photo_redirects_you_to_prepare_info(
    logged_in_client: FlaskClient, app: Flask, flickr_api: FlickrPhotosApi
) -> None:
    flickr_url = "https://www.flickr.com/photos/coast_guard/32812033543/"

    get_photos_data = get_typed_fixture(
        path="flickr_api/single_photo-32812033543.json", model=SinglePhotoData
    )

    cache_id = save_cached_photos_data(get_photos_data)

    resp = logged_in_client.post(
        f"/select_photos?flickr_url={flickr_url}",
        data={"photo_32812033543": "on", "cache_id": cache_id},
    )

    assert resp.status_code == 302
    assert (
        resp.headers["location"]
        == f"/prepare_info?selected_photo_ids=32812033543&cache_id={cache_id}"
    )


def test_selecting_multiple_photo_redirects_you_to_prepare_info(
    logged_in_client: FlaskClient, app: Flask, flickr_api: FlickrPhotosApi
) -> None:
    flickr_url = "https://www.flickr.com/photos/icann/albums/72177720312192106"

    get_photos_data = get_typed_fixture(
        path="flickr_api/album-72177720312192106.json", model=PhotosInAlbumData
    )

    cache_id = save_cached_photos_data(get_photos_data)

    resp = logged_in_client.post(
        f"/select_photos?flickr_url={flickr_url}",
        data={
            "photo_53285005734": "on",
            "photo_53283740177": "on",
            "cache_id": cache_id,
        },
    )

    assert resp.status_code == 302
    assert (
        resp.headers["location"]
        == f"/prepare_info?selected_photo_ids=53285005734,53283740177&cache_id={cache_id}"
    )


def test_you_cant_select_a_restricted_image(
    logged_in_client: FlaskClient, flickr_api: FlickrPhotosApi
) -> None:
    # This is a graphic showing a Buddha quote which is marked as
    # safety level "restricted", so we shouldn't allow somebody to select
    # it for sending to Wikimedia Commons.
    flickr_url = "https://www.flickr.com/photos/free-images-flickr/35856118446"

    resp = logged_in_client.get(f"/select_photos?flickr_url={flickr_url}")

    assert "This photo can’t be used." in resp.data.decode("utf8")
