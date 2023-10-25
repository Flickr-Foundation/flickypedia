import json

import pytest


@pytest.mark.parametrize(
    "url",
    [
        "/select_photos",
        "/select_photos?flickr_url=no",
        "/select_photos?flickr_url=https://example.net",
    ],
)
def test_rejects_pages_with_bad_query_params(logged_in_client, url):
    resp = logged_in_client.get(url)

    assert resp.status_code == 400


def test_can_select_single_photo_on_flickr(logged_in_client, flickr_api):
    resp = logged_in_client.get(
        "/select_photos?flickr_url=https://www.flickr.com/photos/199246608@N02/53253175319/"
    )

    assert resp.status_code == 302
    assert resp.headers["location"].startswith(
        "/prepare_info?selected_photo_ids=53253175319&cached_api_response_id="
    )


def test_duplicate_single_photo_on_flickr_is_not_allowed(logged_in_client, flickr_api):
    resp = logged_in_client.get(
        "/select_photos?flickr_url=https://www.flickr.com/photos/fotnmc/9999819294/"
    )

    assert resp.status_code == 200
    assert b"Your work is done!" in resp.data


def test_single_photo_with_bad_license_is_not_allowed(logged_in_client, flickr_api):
    resp = logged_in_client.get(
        "/select_photos?flickr_url=https://www.flickr.com/photos/ryanschude/50868060871/"
    )

    assert resp.status_code == 200
    assert "This photo can’t be used" in resp.data.decode("utf8")


def test_gets_album_on_flickr(logged_in_client, flickr_api):
    resp = logged_in_client.get(
        "/select_photos?flickr_url=https://www.flickr.com/photos/aljazeeraenglish/albums/72157626164453131/"
    )

    assert resp.status_code == 200
    assert b"by Al Jazeera English" in resp.data


@pytest.mark.parametrize(
    ["url", "error"],
    [
        (
            "https://www.flickr.com/photos/doesnotexist/12345678901234567890",
            b"There is no photo at that URL!",
        )
    ],
)
def test_redirects_to_find_photos_if_non_existent_photo(
    logged_in_client, flickr_api, url, error
):
    """
    If you try to look up a non-existent URL, you should be redirected
    back to the find photos screen, where:

    *   There's an error message about there being no URLs at this page
    *   Your URL is pre-filled in the input box

    """
    resp = logged_in_client.get(f"/select_photos?flickr_url={url}")
    assert resp.status_code == 302
    assert resp.headers["location"] == "/find_photos"

    redirected_resp = logged_in_client.get(resp.headers["location"])
    assert redirected_resp.status_code == 200

    assert error in redirected_resp.data
    assert f'value="{url}"'.encode("ascii") in redirected_resp.data


def test_no_photo_selection_is_error(logged_in_client, flickr_api):
    """
    If you POST a form without a selection, you get an error.
    """
    flickr_url = "https://www.flickr.com/photos/schlesinger_library/13270291833/"

    resp = logged_in_client.post(f"/select_photos?flickr_url={flickr_url}")

    assert resp.status_code == 200
    assert b"You need to select at least one photo!" in resp.data


def test_selecting_photo_redirects_you_to_prepare_info(
    logged_in_client, app, flickr_api
):
    flickr_url = "https://www.flickr.com/photos/coast_guard/32812033543/"

    cache_dir = app.config["FLICKR_API_RESPONSE_CACHE"]

    with open(f"{cache_dir}/1234567890.json", "w") as outfile:
        with open("tests/fixtures/flickr_api/32812033543.json") as infile:
            single_photo_resp = json.load(infile)
        outfile.write(json.dumps({"photos": [single_photo_resp]}))

    resp = logged_in_client.post(
        f"/select_photos?flickr_url={flickr_url}",
        data={"photo_32812033543": "on", "cached_api_response_id": "1234567890"},
    )

    assert resp.status_code == 302
    assert (
        resp.headers["location"]
        == "/prepare_info?selected_photo_ids=32812033543&cached_api_response_id=1234567890"
    )
