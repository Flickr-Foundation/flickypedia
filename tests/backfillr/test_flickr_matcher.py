import pathlib

import pytest

from flickypedia.backfillr.flickr_matcher import (
    AmbiguousStructuredData,
    FindResult,
    find_flickr_photo_id_from_sdc,
    find_flickr_photo_id_from_wikitext,
)
from flickypedia.types.structured_data import ExistingClaims
from utils import get_typed_fixture


@pytest.mark.parametrize(
    ["filename", "photo_id"],
    [
        ("Example.jpg", None),
        #
        # This has a Flickr photo URL in the Wikitext
        (
            "A breezy day in Venice (1890s), by Ettore Tito.png",
            {
                "photo_id": "49800608076",
                "url": "https://www.flickr.com/photos/gandalfsgallery/49800608076/in/photostream/",
            },
        ),
        #
        # This has a Flickr URL in the Wikitext, but it links to
        # the author's profile rather than the photo
        ("The main Flickr photo storage server.jpg", None),
        #
        # This has a Flickr photo ID in the "Source" row of the
        # "Information" table, so we can match it even though the original
        # photo can no longer be downloaded from Flickr.
        (
            "EI-DYY (15602283025).jpg",
            {
                "photo_id": "15602283025",
                "url": "https://www.flickr.com/photos/golfking1/15602283025/",
            },
        ),
        #
        # These have multiple Flickr photo URLs in the Wikitext, and only
        # one of them points to the original photo.
        (
            "Intel 8742 153056995.jpg",
            {
                "photo_id": "153056995",
                "url": "https://www.flickr.com/photos/biwook/153056995/",
            },
        ),
        (
            "Taking photo.jpg",
            {
                "photo_id": "9078889",
                "url": "https://www.flickr.com/photos/48889110751@N01/9078889",
            },
        ),
        #
        # This has Flickr photo URLs in the Wikitext, but they point to
        # different photos.
        ("Graffiti Rosario - Darío y Maxi.jpg", None),
        #
        # This has a Flickr photo ID in the "Source" row of the
        # "Information" table, so we can match it even though the original
        # photo has been deleted from Flickr.
        (
            "Stewart-White line in the road spraying machine.jpg",
            {
                "photo_id": "253009",
                "url": "http://www.flickr.com/photos/stewart/253009/",
            },
        ),
        #
        # This has a Flickr URL in the Wikitext, but the original photo
        # has been deleted and there's nothing to tell us this URL is
        # significant above others.
        ("Stewart-Baseball cropped.jpg", None),
        #
        # This has a Flickr URL in the Wikitext, which is clearly
        # identified as the Source in a paragraph that labels it as such.
        (
            "Dan Potthast.jpg",
            {
                "photo_id": "3731022",
                "url": "https://www.flickr.com/photos/justinaugust/3731022/",
            },
        ),
        #
        # Another Flickr URL in the Wikitext, clearly identified as
        # the source URL in the text.  There's a newline inside the
        # associated <p> tag which we need to account for.
        (
            "Vinyl albums.jpg",
            {
                "photo_id": "3874334",
                "url": "https://www.flickr.com/photos/metalphoenix/3874334/",
            },
        ),
        #
        # Another Flickr URL in the Wikitext, where the link label
        # is just "Flickr".
        (
            "Wild-wadi.jpg",
            {
                "photo_id": "4101549",
                "url": "https://www.flickr.com/photos/saudi/4101549/",
            },
        ),
        #
        # Two Flickr URLs in the "Source" field, one is the user and
        # one is the source.
        (
            "Varanasi 3.jpg",
            None,
        ),
    ],
)
def test_find_flickr_photo_id_from_wikitext(
    filename: str,
    photo_id: FindResult | None,
) -> None:
    with open(f"tests/fixtures/wikitext/{filename}.html") as infile:
        wikitext = infile.read()

    assert photo_id == find_flickr_photo_id_from_wikitext(
        wikitext, filename=f"File:{filename}"
    )


def get_statement_fixture(filename: str) -> ExistingClaims:
    fixtures_dir = pathlib.Path("structured_data/existing")

    return get_typed_fixture(path=fixtures_dir / filename, model=ExistingClaims)


@pytest.mark.parametrize(
    ["filename", "expected_flickr_photo_id"],
    [
        # M138765382 = MarkingOfBooksSign.jpg
        # Retrieved 7 December 2023
        (
            "M138765382_P7482.json",
            {
                "photo_id": "53253175319",
                "url": "https://www.flickr.com/photos/199246608@N02/53253175319/",
            },
        ),
        ("M138765382_P12120.json", {"photo_id": "53253175319", "url": None}),
        #
        # M27512034 = Addicott Electrics (HL08 AEL) DAF CF rigid flatbed with crane, 23 March 2012.jpg
        # Retrieved 8 December 2023
        #
        # The "source of file" field had a "described at URL" qualifier
        # but no "URL" qualifier.
        (
            "M27512034_P7482.json",
            {
                "photo_id": "6868541110",
                "url": "https://www.flickr.com/photos/16179216@N07/6868541110/",
            },
        ),
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
        (
            "M27807191_P7482.json",
            {
                "photo_id": "2675972715",
                "url": "https://www.flickr.com/photos/normanbleventhalmapcenter/2675972715",
            },
        ),
        #
        # M-1 = a made-up record which has a non-string value in the
        # P973 qualifier.  As of the 20231124 snapshot, this never happens
        # in practice, but we want to make sure we handle it all the same.
        ("M-1_P7482_nostring.json", None),
        #
        # M-1 = a made-up record which has a non-Flickr URL in the
        # P973 qualifier.  As of the 20231124 snapshot, this never happens
        # in practice, but we want to make sure we handle it all the same.
        ("M-1_P7482_badurl.json", None),
        #
        # M-1 = a made-up record which has a non-string value in the
        # P12120 property.  As of the 20231124 snapshot, this never happens
        # in practice, but we want to make sure we handle it all the same.
        ("M-1_P12120_nostring.json", None),
        #
        # M16767898 = "Adormirea Sf.Ana - Batiste" - 2.jpg
        # Retrieved 14 December 2023
        #
        # This has a Flickr URL in the "Described at URL" qualifier on P7482,
        # but no "Source" qualifier that tells us it's Flickr.
        (
            "M16767898_P7482.json",
            {
                "photo_id": "5902112330",
                "url": "https://www.flickr.com/photos/claudiunh/5902112330/",
            },
        ),
    ],
)
def test_find_flickr_photo_id_from_sdc(
    filename: str, expected_flickr_photo_id: FindResult | None
) -> None:
    sdc = get_statement_fixture(filename)

    assert find_flickr_photo_id_from_sdc(sdc) == expected_flickr_photo_id


def test_empty_sdc_means_no_flickr_id() -> None:
    assert find_flickr_photo_id_from_sdc(sdc={}) is None


def test_ambiguous_sdc_is_error() -> None:
    sdc_P7482 = get_statement_fixture("M27512034_P7482.json")
    sdc_P12120 = get_statement_fixture("M138765382_P12120.json")

    sdc = {"P12120": sdc_P12120["P12120"], "P7482": sdc_P7482["P7482"]}

    with pytest.raises(ValueError, match="Ambiguous set of Flickr photo IDs:"):
        find_flickr_photo_id_from_sdc(sdc=sdc)


def test_ambiguous_flickr_url_is_error() -> None:
    # M620184 = Metro Madrid Retiro.jpg
    # Retrieved 24 November 2023
    #
    # The "source of file" field links to the Flickr user's profile rather
    # than the individual photo in the "URL" qualifier.
    sdc = get_statement_fixture("M620184_P7482.json")

    with pytest.raises(AmbiguousStructuredData):
        find_flickr_photo_id_from_sdc(sdc)


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
        find_flickr_photo_id_from_sdc(sdc)
