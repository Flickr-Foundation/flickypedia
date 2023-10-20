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


def test_gets_single_photo_on_flickr(logged_in_client, flickr_api):
    resp = logged_in_client.get(
        "/select_photos?flickr_url=https://www.flickr.com/photos/schlesinger_library/13270291833/"
    )

    assert resp.status_code == 200
    assert b"Mae_Eberhardt" in resp.data


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
