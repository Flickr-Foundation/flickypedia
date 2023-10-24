from flickypedia.duplicates import create_media_search_link, find_duplicates


def test_no_flickr_photo_ids_is_no_duplicates(client):
    assert find_duplicates(flickr_photo_ids=[]) == []


def test_finds_single_flickr_photo_id(client):
    assert find_duplicates(flickr_photo_ids=["9999819294"]) == [
        ("9999819294", "M29907038")
    ]


def test_finds_multiple_flickr_photo_ids(client):
    actual = find_duplicates(
        flickr_photo_ids=[
            "9999819294",
            "9999868886",
            "9999416633",
            "9999408183",
            "1234",
        ]
    )
    expected = [
        ("9999819294", "M29907038"),
        ("9999868886", "M29907062"),
        ("9999416633", "M29907327"),
        ("9999408183", "M29907338"),
    ]

    assert actual == expected


def test_create_media_search_link(client):
    duplicates = find_duplicates(
        flickr_photo_ids=[
            "9999819294",
            "9999868886",
            "9999416633",
            "9999408183",
        ]
    )

    assert (
        create_media_search_link(duplicates)
        == "https://commons.wikimedia.org/wiki/Special:MediaSearch?type=image&search=pageid:29907038|29907062|29907327|29907338"
    )
