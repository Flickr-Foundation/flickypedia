def test_renders_basic_page(logged_in_client):
    resp = logged_in_client.get("/find_photos")

    assert resp.status_code == 200
    assert b"Enter a Flickr URL" in resp.data


def test_rejects_a_non_flickr_url(logged_in_client):
    resp = logged_in_client.post(
        "/find_photos", data={"flickr_url": "https://example.net"}
    )

    assert resp.status_code == 200

    assert b"Enter a Flickr URL" in resp.data
    assert "That URL doesn’t live on Flickr.com" in resp.data.decode("utf8")


def test_rejects_a_non_photo_flickr_url(logged_in_client):
    resp = logged_in_client.post(
        "/find_photos", data={"flickr_url": "https://flickr.com/help"}
    )

    assert resp.status_code == 200

    assert b"Enter a Flickr URL" in resp.data
    assert b"There are no photos to show at that URL" in resp.data


def test_redirects_if_photo_url(logged_in_client):
    flickr_url = "https://www.flickr.com/photos/schlesinger_library/13270291833"

    resp = logged_in_client.post("/find_photos", data={"flickr_url": flickr_url})

    assert resp.status_code == 302
    assert resp.headers["location"] == f"/select_photos?flickr_url={flickr_url}"
