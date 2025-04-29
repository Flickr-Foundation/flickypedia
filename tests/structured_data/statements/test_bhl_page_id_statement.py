from datetime import datetime, timezone

from flickr_api import FlickrApi
from flickr_api.models import MachineTags
import pytest

from flickypedia.structured_data import create_sdc_claims_for_new_flickr_photo
from flickypedia.structured_data.statements.bhl_page_id_statement import (
    create_bhl_page_id_statement,
    guess_bhl_page_id,
)


@pytest.mark.parametrize(
    ["photo_id", "machine_tags", "page_id"],
    [
        (
            "51281775881",
            {"bhl:page": ["33665645"]},
            "33665645",
        ),
        (
            "51269075642",
            {"bhl:page": ["61831901"]},
            "61831901",
        ),
        (
            "49841872056",
            {"bhl:page": ["52948312"]},
            "52948312",
        ),
        (
            "46016620675",
            {"bhl:page": ["54052811"]},
            "54052811",
        ),
        (
            "36561149543",
            {"bhl:page": ["53071515"]},
            "53071515",
        ),
        (
            "7982377911",
            {"bhl:page": ["4321212"]},
            "4321212",
        ),
        ("5665412449", {"taxonomy:binomial": ["aegothelessavesi"]}, None),
        (
            "5984633427",
            {"bhl:page": ["34021551", "34551619"]},
            None,
        ),
    ],
)
def test_guess_bhl_page_id(
    photo_id: str, machine_tags: MachineTags, page_id: str | None
) -> None:
    assert guess_bhl_page_id(photo_id=photo_id, machine_tags=machine_tags) == page_id


def test_creates_bhl_page_id_statement() -> None:
    statement = create_bhl_page_id_statement(
        photo_id="7982377911", machine_tags={"bhl:page": ["4321212"]}
    )

    assert statement == {
        "mainsnak": {
            "datavalue": {"value": "4321212", "type": "string"},
            "property": "P687",
            "snaktype": "value",
        },
        "type": "statement",
    }


def test_does_not_create_bhl_page_id_statement_if_no_pageid() -> None:
    statement = create_bhl_page_id_statement(
        photo_id="5665412449",
        machine_tags={"taxonomy:binomial": ["aegothelessavesi"]},
    )

    assert statement is None


class TestClaims:
    def test_includes_statement_if_bhl_user(self, flickr_api: FlickrApi) -> None:
        photo = flickr_api.get_single_photo(photo_id="7982377911")

        statement = create_bhl_page_id_statement(
            photo_id=photo["id"], machine_tags=photo["machine_tags"]
        )
        assert statement is not None

        claims = create_sdc_claims_for_new_flickr_photo(
            photo, retrieved_at=datetime.now(tz=timezone.utc)
        )

        assert statement in claims["claims"]

    def test_omits_statement_if_not_bhl_user(self, flickr_api: FlickrApi) -> None:
        photo = flickr_api.get_single_photo(photo_id="7982377911")

        statement = create_bhl_page_id_statement(
            photo_id=photo["id"], machine_tags=photo["machine_tags"]
        )
        assert statement is not None

        photo["owner"]["id"] = "-1"

        claims = create_sdc_claims_for_new_flickr_photo(
            photo, retrieved_at=datetime.now(tz=timezone.utc)
        )

        assert statement not in claims["claims"]
        assert not any(
            statement["mainsnak"]["property"] == "P687"
            for statement in claims["claims"]
        )

    def test_omits_statement_if_no_pageid_tag(self, flickr_api: FlickrApi) -> None:
        photo = flickr_api.get_single_photo(photo_id="7982377911")
        photo["machine_tags"] = {}

        statement = create_bhl_page_id_statement(
            photo_id=photo["id"], machine_tags=photo["machine_tags"]
        )
        assert statement is None

        claims = create_sdc_claims_for_new_flickr_photo(
            photo, retrieved_at=datetime.now(tz=timezone.utc)
        )

        assert not any(
            statement["mainsnak"]["property"] == "P687"
            for statement in claims["claims"]
        )
