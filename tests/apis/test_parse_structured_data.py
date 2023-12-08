import pathlib

import pytest

from flickypedia.apis.structured_data import AmbiguousStructuredData, find_flickr_photo_id
from flickypedia.types.structured_data import ExistingClaims
from utils import get_typed_fixture


def get_statement_fixture(filename: str) -> ExistingClaims:
    fixtures_dir = pathlib.Path("structured_data/existing")

    return get_typed_fixture(path=fixtures_dir / filename, model=ExistingClaims)


@pytest.mark.parametrize(
    ["filename", "expected_flickr_photo_id"],
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
        #
        # M27807191 = Nationalist government of Nanking - nominally ruling over entire China, 1930 (2675972715).jpg
        # Retrieved 8 December 2023
        #
        # There are two "source of file" fields, one of which is a Flickr URL.
        ("M27807191_P7482.json", "2675972715"),
    ],
)
def test_find_flickr_photo_id(
    filename: str, expected_flickr_photo_id: str | None
) -> None:
    sdc = get_statement_fixture(filename)

    assert find_flickr_photo_id(sdc) == expected_flickr_photo_id


def test_empty_sdc_means_no_flickr_id() -> None:
    assert find_flickr_photo_id(sdc={}) is None


def test_ambiguous_flickr_url_is_error() -> None:
    # M620184 = Metro Madrid Retiro.jpg
    # Retrieved 24 November 2023
    #
    # The "source of file" field links to the Flickr user's profile rather
    # than the individual photo in the "URL" qualifier.
    sdc = get_statement_fixture("M620184_P7482.json")

    with pytest.raises(AmbiguousStructuredData):
        find_flickr_photo_id(sdc)


def test_ambiguous_qualifier_is_error() -> None:
    # M15393706 = Carel Fabritius - The Goldfinch - WGA7721.jpg
    # Retrieved 24 November 2023
    #
    # The "source of file" field has multiple values for the "Operator"
    # and "Described at URL" qualifier.
    #
    # I fixed the qualifiers in the Wikimedia data by splitting them
    # into two statements, but we need to make sure we don't crash
    # when this occurs.
    sdc = get_statement_fixture("M15393706_P7482.json")

    with pytest.raises(AmbiguousStructuredData):
        find_flickr_photo_id(sdc)
