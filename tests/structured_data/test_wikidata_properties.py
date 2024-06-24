import pytest

from flickypedia.structured_data import get_wikidata_property_label


@pytest.mark.parametrize(
    ["id", "label"],
    [
        ("P571", "date created"),
        ("P1259", "location"),
        ("P170", "creator"),
        ("P577", "publication date"),
    ],
)
def test_get_wikidata_property_label(id: str, label: str) -> None:
    assert get_wikidata_property_label(id) == label


def test_unrecognised_property_id_is_error() -> None:
    with pytest.raises(KeyError, match="Unrecognised property ID"):
        get_wikidata_property_label(id="P0")
