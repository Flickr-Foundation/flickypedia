import pathlib

import pytest

from flickypedia.apis.structured_data import find_flickr_photo_id
from flickypedia.types.structured_data import ExistingClaims
from utils import get_typed_fixture


def get_statement_fixture(filename: str) -> ExistingClaims:
    fixtures_dir = pathlib.Path("structured_data/existing")

    return get_typed_fixture(path=fixtures_dir / filename, model=ExistingClaims)



@pytest.mark.parametrize(["filename", "expected_flickr_photo_id"],
[
    # M138765382 = MarkingOfBooksSign.jpg
    # Retrieved 7 December 2023
    ("M138765382_P7482.json", "53253175319"),
    ("M138765382_P12120.json", "53253175319"),
    #
    # M27512034 = Addicott Electrics (HL08 AEL) DAF CF rigid flatbed with crane, 23 March 2012.jpg
    # Retrieved 8 December 2023
    #
    # The "source of file" field had a "described at URL" qualifier
    # but no "URL" qualifier.
    ("M27512034_P7482.json", "6868541110"),
    #
    # M76 = Bustaxi.jpg
    # Retrieved 24 November 2023
    ("M76_P7482.json", None),
    #
    # M423 = Fabritius-vink.jpg
    # Retrieved 24 November 2023
    #
    # The "source of file" field has a non-Flickr value in
    # the "Operator" qualifier
    ("M423_P7482.json", None),
])
def test_find_flickr_photo_id(filename: str, expected_flickr_photo_id: str | None) -> None:
    sdc = get_statement_fixture(filename)

    assert find_flickr_photo_id(sdc) == expected_flickr_photo_id


def test_empty_sdc_means_no_flickr_id() -> None:
    assert find_flickr_photo_id(sdc={}) is None
