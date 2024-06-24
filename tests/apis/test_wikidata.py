import pytest

from flickypedia.apis.wikidata import get_flickr_user_id


@pytest.mark.parametrize(
    ["entity_id", "user_id"], [("Q33132025", "65001151@N03"), ("Q33132026", None)]
)
def test_get_flickr_user_id(
    vcr_cassette: None, entity_id: str, user_id: str | None
) -> None:
    assert get_flickr_user_id(entity_id=entity_id) == user_id
