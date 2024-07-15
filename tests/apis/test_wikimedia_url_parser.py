import pytest

from flickypedia.apis.wikimedia import get_filename_from_url


@pytest.mark.parametrize(
    "url",
    [
        "https://example.net",
        "https://commons.wikimedia.org/",
        "https://commons.wikimedia.org/wiki/Category:Flickr_images_missing_SDC_creator",
        "https://commons.wikimedia.org/w/index.php",
    ],
)
def test_it_rejects_non_file_urls(url: str) -> None:
    with pytest.raises(ValueError):
        get_filename_from_url(url)


@pytest.mark.parametrize(
    ["url", "filename"],
    [
        pytest.param(
            "https://commons.wikimedia.org/wiki/File:Portogallo_2007_(1677680909).jpg",
            "Portogallo_2007_(1677680909).jpg",
            id="Portogallo",
        ),
        pytest.param(
            "https://commons.wikimedia.org/wiki/File:%225_April_2017_-_The_Culture_defense_(34175959031).jpg",
            '"5_April_2017_-_The_Culture_defense_(34175959031).jpg',
            id="The_Culture_defense",
        ),
        pytest.param(
            "https://commons.m.wikimedia.org/wiki/File:%22Christmas_wishes%22_-_Christmas_card._Nellie_Murrell_Collection,_Australia_c._1900s.jpg",
            '"Christmas_wishes"_-_Christmas_card._Nellie_Murrell_Collection,_Australia_c._1900s.jpg',
            id="Christmas_wishes",
        ),
        pytest.param(
            "https://commons.wikimedia.org/?curid=106460733",
            "View of Mount Lycabettus from Ardettus Hill in Athens on June 10, 2021.jpg",
            id="Mount Lycabettus",
        ),
    ],
)
def test_it_gets_filename_from_url(vcr_cassette: str, url: str, filename: str) -> None:
    assert get_filename_from_url(url) == filename
