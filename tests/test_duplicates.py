from flickypedia.duplicates import create_media_search_link, find_duplicates


def test_no_flickr_photo_ids_is_no_duplicates(client):
    assert find_duplicates(flickr_photo_ids=[]) == []


def test_finds_single_flickr_photo_id(client):
    assert find_duplicates(flickr_photo_ids=["53240661807"]) == [
        (
            "53240661807",
            {
                "page_id": "M138598125",
                "title": "File:Volvo 940 Estate (53240661807).jpg",
            },
        )
    ]


def test_finds_multiple_flickr_photo_ids(client):
    actual = find_duplicates(
        flickr_photo_ids=[
            "53240661807",
            "53240662130",
            "53240718409",
            "53240762226",
            "1234",
        ]
    )
    expected = [
        (
            "53240661807",
            {
                "page_id": "M138598125",
                "title": "File:Volvo 940 Estate (53240661807).jpg",
            },
        ),
        (
            "53240662130",
            {
                "page_id": "M138576742",
                "title": "File:Barrage Vauban August 2023 DT 05.jpg",
            },
        ),
        (
            "53240718409",
            {
                "page_id": "M138599027",
                "title": "File:Day 17 Cheetah (Acinonyx jubatus) cub ... (53240718409).jpg",
            },
        ),
        ("53240762226", {"page_id": "M138584414", "title": "File:Img monochrome.jpg"}),
    ]

    assert actual == expected


def test_create_media_search_link(client):
    duplicates = find_duplicates(
        flickr_photo_ids=[
            "53240661807",
            "53240662130",
            "53240718409",
            "53240762226",
            "1234",
        ]
    )

    assert (
        create_media_search_link(duplicates)
        == "https://commons.wikimedia.org/wiki/Special:MediaSearch?type=image&search=pageid:138598125|138576742|138599027|138584414"
    )
