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
