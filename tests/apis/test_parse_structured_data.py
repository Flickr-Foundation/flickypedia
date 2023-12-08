import pathlib

from flickypedia.apis.structured_data import find_flickr_photo_id
from flickypedia.types.structured_data import ExistingClaims
from utils import get_typed_fixture


def get_statement_fixture(filename: str) -> ExistingClaims:
    fixtures_dir = pathlib.Path("structured_data/existing")

    return get_typed_fixture(path=fixtures_dir / filename, model=ExistingClaims)


class TestFindFlickrPhotoId:
    def test_empty_sdc_means_no_flickr_id(self) -> None:
        assert find_flickr_photo_id(sdc={}) is None

    def test_can_find_flickr_id_in_source(self) -> None:
        # M138765382 = MarkingOfBooksSign.jpg
        # Retrieved 7 December 2023
        sdc = get_statement_fixture("M138765382_P7482.json")

        assert find_flickr_photo_id(sdc) == "53253175319"

    def test_can_find_flickr_id_in_photo_id(self) -> None:
        # M138765382 = MarkingOfBooksSign.jpg
        # Retrieved 7 December 2023
        sdc = get_statement_fixture("M138765382_P12120.json")

        assert find_flickr_photo_id(sdc) == '53253175319'

    def test_can_find_flickr_id_with_no_url_in_source(self) -> None:
        # M27512034 = Addicott Electrics (HL08 AEL) DAF CF rigid flatbed with crane, 23 March 2012.jpg
        # Retrieved 8 December 2023
        #
        # The "source of file" field had a "described at URL" qualifier
        # but no "URL" qualifier.
        sdc = get_statement_fixture("M27512034_P7482.json")

        assert find_flickr_photo_id(sdc) == '6868541110'