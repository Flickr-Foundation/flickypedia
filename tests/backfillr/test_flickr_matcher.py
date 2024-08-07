import pytest

from flickypedia.apis import WikimediaApi
from flickypedia.backfillr.flickr_matcher import (
    AmbiguousStructuredData,
    FindResult,
    find_flickr_photo_id_from_sdc,
    find_flickr_photo_id_from_wikitext,
)
from utils import get_existing_claims_fixture


@pytest.mark.parametrize(
    ["filename", "photo_id"],
    [
        pytest.param("Example.jpg", None, id="example"),
        #
        # This has a Flickr photo URL in the Wikitext
        pytest.param(
            "A breezy day in Venice (1890s), by Ettore Tito.png",
            {
                "photo_id": "49800608076",
                "url": "https://www.flickr.com/photos/gandalfsgallery/49800608076/in/photostream/",
            },
            id="49800608076",
        ),
        #
        # This has a Flickr URL in the Wikitext, but it links to
        # the author's profile rather than the photo
        pytest.param(
            "The main Flickr photo storage server.jpg", None, id="flickr_server"
        ),
        #
        # This has a Flickr photo ID in the "Source" row of the
        # "Information" table, so we can match it even though the original
        # photo can no longer be downloaded from Flickr.
        pytest.param(
            "EI-DYY (15602283025).jpg",
            {
                "photo_id": "15602283025",
                "url": "https://www.flickr.com/photos/golfking1/15602283025/",
            },
            id="15602283025",
        ),
        #
        # These have multiple Flickr photo URLs in the Wikitext, and only
        # one of them points to the original photo.
        pytest.param(
            "Intel 8742 153056995.jpg",
            {
                "photo_id": "153056995",
                "url": "https://www.flickr.com/photos/biwook/153056995/",
            },
            id="153056995",
        ),
        pytest.param(
            "Taking photo.jpg",
            {
                "photo_id": "9078889",
                "url": "https://www.flickr.com/photos/48889110751@N01/9078889",
            },
            id="9078889",
        ),
        #
        # This has Flickr photo URLs in the Wikitext, but they point to
        # different photos.
        pytest.param("Graffiti Rosario - Darío y Maxi.jpg", None, id="graffiti_rosari"),
        #
        # This has a Flickr photo ID in the "Source" row of the
        # "Information" table, so we can match it even though the original
        # photo has been deleted from Flickr.
        pytest.param(
            "Stewart-White line in the road spraying machine.jpg",
            {
                "photo_id": "253009",
                "url": "http://www.flickr.com/photos/stewart/253009/",
            },
            id="253009",
        ),
        #
        # This has a Flickr URL in the Wikitext, but the original photo
        # has been deleted and there's nothing to tell us this URL is
        # significant above others.
        pytest.param("Stewart-Baseball cropped.jpg", None, id="stewart-baseball"),
        # This has a Flickr URL in the Wikitext, which is clearly
        # identified as the Source in a paragraph that labels it as such.
        pytest.param(
            "Dan Potthast.jpg",
            {
                "photo_id": "3731022",
                "url": "https://www.flickr.com/photos/justinaugust/3731022/",
            },
            id="3731022",
        ),
        #
        # Another Flickr URL in the Wikitext, clearly identified as
        # the source URL in the text.  There's a newline inside the
        # associated <p> tag which we need to account for.
        pytest.param(
            "Vinyl albums.jpg",
            {
                "photo_id": "3874334",
                "url": "https://www.flickr.com/photos/metalphoenix/3874334/",
            },
            id="3874334",
        ),
        #
        # Another Flickr URL in the Wikitext, where the link label
        # is just "Flickr".
        pytest.param(
            "Wild-wadi.jpg",
            {
                "photo_id": "4101549",
                "url": "https://www.flickr.com/photos/saudi/4101549/",
            },
            id="4101549",
        ),
        #
        # Two Flickr URLs in the "Source" field, one is the user and
        # one is the source.
        pytest.param("Varanasi 3.jpg", None, id="varanasi_3"),
        #
        # Two Flickr URLs in the "Source" field, one is a raw Flickr URL
        # and one is the source.
        pytest.param(
            "In Chinatown, San Francisco.jpg",
            {
                "photo_id": "869031",
                "url": "https://www.flickr.com/photos/51035573370@N01/869031",
            },
            id="869031",
        ),
        #
        # Two URLs in the "Source" field, neither of them from Flickr.
        pytest.param("Pierre Riel de Beurnonville (1792).jpg", None, id="pierre_riel"),
    ],
)
def test_find_flickr_photo_id_from_wikitext(
    wikimedia_api: WikimediaApi,
    filename: str,
    photo_id: FindResult | None,
) -> None:
    wikitext = wikimedia_api.get_wikitext(filename=f"File:{filename}")

    assert photo_id == find_flickr_photo_id_from_wikitext(
        wikitext, filename=f"File:{filename}"
    )


@pytest.mark.parametrize(
    ["wikitext", "photo_id"],
    [
        # This covers the case where there are two links in the Source field and
        # the first is the Flickr homepage, but the second isn't a link to
        # a Flickr photo.
        (
            """
            <tr>
              <td class="fileinfo-paramfield" id="fileinfotpl_src" lang="en">Source</td>
              <td>
                <a href="https://www.flickr.com/">Flickr.com</a> /
                <a href="https://en.wikipedia.org/wiki/Flickr">Flickr</a>
              </td>
            </tr>
            """,
            None,
        ),
        # This covers the case where the first URL in the Source field is
        # a link to the Wikipedia page for Flickr.
        (
            """
            <tr>
              <td id="fileinfotpl_src" class="fileinfo-paramfield" lang="en">Source</td>
              <td>
                 <a href="/wiki/Flickr" class="mw-redirect" title="Flickr">Flickr</a>:
                 <a rel="nofollow" class="external text" href="https://www.flickr.com/photos/25834786@N03/3598534263">polling station</a>
              </td>
            </tr>
            """,
            {
                "photo_id": "3598534263",
                "url": "https://www.flickr.com/photos/25834786@N03/3598534263",
            },
        ),
        (
            """
            <tr>
              <td id="fileinfotpl_src" class="fileinfo-paramfield" lang="en">Source</td>
              <td>
                 <a href="/wiki/Flickr" class="mw-redirect" title="Flickr">Flickr</a>:
                 <a rel="nofollow" class="external text" href="https://www.flickr.com/photos/25834786@N03">a link to a user</a>
              </td>
            </tr>
            """,
            None,
        ),
    ],
)
def test_find_flickr_photo_id_from_static_wikitext(
    wikitext: str, photo_id: FindResult | None
) -> None:
    assert photo_id == find_flickr_photo_id_from_wikitext(
        wikitext, filename="File:Example.jpg"
    )


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
        #
        # M51747012 = HS Familjeliv 1917 279, 1917 (16041507752).jpg
        # Retrieved 21 May 2024
        #
        # This is an example of a photo from the National Library of Finland,
        # which structures the Source of File field in an unusual way.
        pytest.param(
            "M51747012_P7482.json",
            {
                "photo_id": "16041507752",
                "url": "https://www.flickr.com/photos/finnishnationalgallery/16041507752/",
            },
            id="finnishnationalgallery",
        ),
    ],
)
def test_find_flickr_photo_id_from_sdc(
    filename: str, expected_flickr_photo_id: FindResult | None
) -> None:
    sdc = get_existing_claims_fixture(filename)

    assert find_flickr_photo_id_from_sdc(sdc) == expected_flickr_photo_id


def test_empty_sdc_means_no_flickr_id() -> None:
    assert find_flickr_photo_id_from_sdc(sdc={}) is None


def test_ambiguous_sdc_is_error() -> None:
    sdc_P7482 = get_existing_claims_fixture("M27512034_P7482.json")
    sdc_P12120 = get_existing_claims_fixture("M138765382_P12120.json")

    sdc = {"P12120": sdc_P12120["P12120"], "P7482": sdc_P7482["P7482"]}

    with pytest.raises(ValueError, match="Ambiguous set of Flickr photo IDs:"):
        find_flickr_photo_id_from_sdc(sdc=sdc)


def test_ambiguous_flickr_url_is_error() -> None:
    # M620184 = Metro Madrid Retiro.jpg
    # Retrieved 24 November 2023
    #
    # The "source of file" field links to the Flickr user's profile rather
    # than the individual photo in the "URL" qualifier.
    sdc = get_existing_claims_fixture("M620184_P7482.json")

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
    sdc = get_existing_claims_fixture("M15393706_P7482.json")

    with pytest.raises(AmbiguousStructuredData):
        find_flickr_photo_id_from_sdc(sdc)


def test_it_handles_a_some_value_string() -> None:
    # M52096071 = Alexander Isak (training 2016, cropped 1).jpg
    # Retrieved 7 May 2024
    #
    # The "source of file" field has an "Operator" qualifier which is
    # just the string value "some value".  I'm fairly sure this is a bug,
    # but it was breaking some code that expected there to be a datavalue
    # there instead.
    sdc = get_existing_claims_fixture("M52096071_P7482.json")

    assert find_flickr_photo_id_from_sdc(sdc) is None


def test_handles_multiple_described_at_urls() -> None:
    # M113422 = RMS Lusitania deck plans.jpg
    # Retrieved 7 May 2024
    #
    # This has multiple instances of the P973 qualifier, but none of them
    # are Flickr URLs so we don't actually care about them.
    sdc = get_existing_claims_fixture("M113422_P7482.json")

    assert find_flickr_photo_id_from_sdc(sdc) is None
