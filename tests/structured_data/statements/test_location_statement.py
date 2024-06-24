from flickr_photos_api import LocationInfo
import pytest

from flickypedia.structured_data import create_sdc_claims_for_new_flickr_photo
from flickypedia.structured_data.statements import create_location_statement
from flickypedia.types.flickr import SinglePhotoData
from utils import get_statement_fixture, get_typed_fixture


def test_unrecognised_location_accuracy_is_error() -> None:
    with pytest.raises(ValueError, match="Unrecognised location accuracy"):
        create_location_statement(
            location={"latitude": 8.079310, "longitude": 77.550004, "accuracy": -1}
        )


@pytest.mark.parametrize(
    ["location", "filename"],
    [
        (
            {"latitude": 9.135158, "longitude": 40.083811, "accuracy": 16},
            "location_ethiopia.json",
        ),
    ],
)
def test_create_location_statement(location: LocationInfo, filename: str) -> None:
    actual = create_location_statement(location=location)
    expected = get_statement_fixture(filename)

    assert actual == expected


def test_omits_location_statement_if_photo_has_no_location_data() -> None:
    data = get_typed_fixture(
        path="flickr_api/single_photo-32812033543.json", model=SinglePhotoData
    )

    sdc = create_sdc_claims_for_new_flickr_photo(
        photo=data["photos"][0], retrieved_at=data["retrieved_at"]
    )

    assert not any(
        statement["mainsnak"]["property"] == "P1259" for statement in sdc["claims"]
    )


def test_includes_location_statement_if_photo_has_location_data() -> None:
    data = get_typed_fixture(
        path="flickr_api/single_photo-52994452213.json", model=SinglePhotoData
    )

    sdc = create_sdc_claims_for_new_flickr_photo(
        photo=data["photos"][0], retrieved_at=data["retrieved_at"]
    )

    location_statements = [
        statement
        for statement in sdc["claims"]
        if statement["mainsnak"]["property"] == "P1259"
    ]

    assert len(location_statements) == 1


def test_no_location_statement_if_no_location_data() -> None:
    assert create_location_statement(location=None) is None


def test_no_location_statement_if_null_location_data() -> None:
    """
    Regression test for https://github.com/Flickr-Foundation/flickypedia/issues/461
    """
    # From https://www.flickr.com/photos/ed_webster/16125227798/
    # Retrieved 23 June 2024
    location: LocationInfo = {"accuracy": 16, "latitude": 0.0, "longitude": 0.0}

    assert create_location_statement(location=location) is None
