"""
Tests for the duplicate detection code.

The real SQLite database is ~1.35GB in size, far too big to check
into the tests.  Instead, a minified version was created by running
the following commands in the 20231009 snapshot:

    sqlite> SELECT COUNT(*) FROM flickr_photos_on_wikimedia;
    11887609
    sqlite> DELETE FROM flickr_photos_on_wikimedia LIMIT 11887409;
    sqlite> VACUUM;

This removes all but 200 entries from the database, creating a 29KB
file we can add to the Git repo for testing.

"""

from flask.testing import FlaskClient

from flickypedia.duplicates import (
    create_link_to_commons,
    find_duplicates,
    record_file_created_by_flickypedia,
)


def test_no_flickr_photo_ids_is_no_duplicates(client: FlaskClient) -> None:
    assert find_duplicates(flickr_photo_ids=[]) == {}


def test_finds_single_flickr_photo_id(client: FlaskClient) -> None:
    assert find_duplicates(flickr_photo_ids=["9999819294"]) == {
        "9999819294": {
            "id": "M29907038",
            "title": "File:Museu da Ciência (9999819294).jpg",
        }
    }


def test_finds_multiple_flickr_photo_ids(client: FlaskClient) -> None:
    actual = find_duplicates(
        flickr_photo_ids=[
            "9999819294",
            "9999868886",
            "9999416633",
            "9999408183",
            "1234",
        ]
    )
    expected = {
        "9999819294": {
            "id": "M29907038",
            "title": "File:Museu da Ciência (9999819294).jpg",
        },
        "9999868886": {
            "id": "M29907062",
            "title": "File:Coimbra auqaduct (9999868886).jpg",
        },
        "9999416633": {
            "id": "M29907327",
            "title": "File:Casa da Música (9999416633) (2).jpg",
        },
        "9999408183": {
            "id": "M29907338",
            "title": "File:Casa da Música (9999408183) (2).jpg",
        },
    }

    assert actual == expected


def test_create_link_to_commons(client: FlaskClient) -> None:
    duplicates = find_duplicates(flickr_photo_ids=["9999819294"])

    assert (
        create_link_to_commons(list(duplicates.values()))
        == "https://commons.wikimedia.org/wiki/File:Museu da Ciência (9999819294).jpg"
    )


def test_create_link_to_commons_for_multiple_ids(client: FlaskClient) -> None:
    duplicates = find_duplicates(
        flickr_photo_ids=[
            "9999819294",
            "9999868886",
            "9999416633",
            "9999408183",
        ]
    )

    assert (
        create_link_to_commons(list(duplicates.values()))
        == "https://commons.wikimedia.org/wiki/Special:MediaSearch?type=image&search=pageid:29907038|29907062|29907327|29907338"
    )


def test_records_files_uploaded_by_flickypedia(client: FlaskClient) -> None:
    assert find_duplicates(flickr_photo_ids=["123"]) == {}

    record_file_created_by_flickypedia(
        flickr_photo_id="123",
        wikimedia_page_title="File:Example.jpg",
        wikimedia_page_id="M123",
    )

    assert find_duplicates(flickr_photo_ids=["123"]) == {
        "123": {"id": "M123", "title": "File:Example.jpg"}
    }
