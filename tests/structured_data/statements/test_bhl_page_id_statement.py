import pytest

from flickypedia.structured_data.statements.bhl_page_id_statement import (
    guess_bhl_page_id,
)


@pytest.mark.parametrize(
    ["photo_id", "tags", "page_id"],
    [
        (
            "51281775881",
            ["periodicals", "physicalsciences", "bhl:page=33665645"],
            "33665645",
        ),
        (
            "51269075642",
            [
                "england",
                "paleontology",
                "bhl:page=61831901",
            ],
            "61831901",
        ),
        (
            "49841872056",
            ["salamanders", "earlyworks", "bhl:page=52948312"],
            "52948312",
        ),
        (
            "46016620675",
            ["australia", "newsouthwales", "bhl:page=54052811"],
            "54052811",
        ),
        (
            "36561149543",
            ["bhl:page=53071515", "butterflies", "insects"],
            "53071515",
        ),
        (
            "7982377911",
            ["austria", "cryptogamia", "bhl:page=4321212"],
            "4321212",
        ),
        ("5665412449", ["taxonomy:binomial=aegothelessavesi", "twitterpost"], None),
        (
            "5984633427",
            ["indonesia", "mammals", "bhl:page=34021551", "bhl:page=34551619"],
            None,
        ),
    ],
)
def test_guess_bhl_page_id(photo_id: str, tags: list[str], page_id: str | None) -> None:
    assert guess_bhl_page_id(photo_id=photo_id, tags=tags) == page_id
