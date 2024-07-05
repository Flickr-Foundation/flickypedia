from flickr_photos_api import FlickrApi
import pytest

from flickypedia.apis import WikimediaApi
from flickypedia.backfillr.backfillr import Backfillr


@pytest.fixture
def backfillr(flickr_api: FlickrApi, wikimedia_api: WikimediaApi) -> Backfillr:
    return Backfillr(flickr_api=flickr_api, wikimedia_api=wikimedia_api)


class TestBackfillr:
    def test_does_nothing_for_already_backfilled_file(
        self, wikimedia_api: WikimediaApi, backfillr: Backfillr
    ) -> None:
        filename = "Momma Cat in the living room 11 (48771463782).jpg"

        before_claims = wikimedia_api.get_structured_data(filename=filename)

        assert all(
            a["action"] == "do_nothing"
            for a in backfillr.update_file(filename=filename)
        )

        after_claims = wikimedia_api.get_structured_data(filename=filename)

        assert before_claims == after_claims

    def test_raises_error_if_cannot_find_flickr_id(self, backfillr: Backfillr) -> None:
        with pytest.raises(ValueError, match="Unable to find Flickr ID"):
            backfillr.update_file(filename="Katscha February 2017 06.jpg")

    def test_it_only_adds_flickr_photo_id_if_original_photo_deleted(
        self, wikimedia_api: WikimediaApi, backfillr: Backfillr
    ) -> None:
        # This file on Wikimedia Commons links to a now-deleted Flickr photo.
        # Retrieved 5 July 2024
        filename = "Olonadé - A Cena Negra Brasileira (Teatro Cacilda Becker) (7).jpg"

        before_claims = wikimedia_api.get_structured_data(filename=filename)
        assert "P12120" not in before_claims

        actions = backfillr.update_file(filename=filename)
        assert len(actions) == 1
        assert actions[0]
        assert actions == [
            {
                "property_id": "P12120",
                "action": "add_missing",
                "statement": {
                    "mainsnak": {
                        "datavalue": {"value": "28952265972", "type": "string"},
                        "property": "P12120",
                        "snaktype": "value",
                    },
                    "type": "statement",
                },
            }
        ]

        after_claims = wikimedia_api.get_structured_data(filename=filename)
        assert "P12120" in after_claims
