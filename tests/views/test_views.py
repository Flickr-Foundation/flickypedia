def test_can_load_about_page(client):
    resp = client.get("/about/")

    assert b"<h2>About Flickypedia</h2>" in resp.data


def test_can_load_bookmarklet(client):
    resp = client.get("/bookmarklet/")

    assert b"<h2>Flickypedia bookmarklet</h2>" in resp.data

