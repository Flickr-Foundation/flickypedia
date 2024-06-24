from flickypedia.structured_data.statements import create_flickr_photo_id_statement


def test_create_flickr_photo_id_statement() -> None:
    statement = create_flickr_photo_id_statement(photo_id="1234567")

    assert statement == {
        "mainsnak": {
            "datavalue": {"value": "1234567", "type": "string"},
            "property": "P12120",
            "snaktype": "value",
        },
        "type": "statement",
    }
