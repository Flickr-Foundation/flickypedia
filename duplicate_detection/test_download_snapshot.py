from download_snapshot import find_links


def test_find_links():
    html = """
            <a href="https://example.net">
            <a href="https://flickr.com/hello">
            <a href="./Cat.jpg">
            <a onclick="alert('boo!');">
        """

    assert find_links(html) == {
        "https://example.net",
        "https://flickr.com/hello",
        "./Cat.jpg",
    }
