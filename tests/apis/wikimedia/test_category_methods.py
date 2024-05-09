from flickypedia.apis import WikimediaApi


def test_find_matching_categories(wikimedia_api: WikimediaApi) -> None:
    result = wikimedia_api.find_matching_categories(query="a")

    assert result == [
        "A",
        "Amsterdam in the 1810s",
        "Aircraft of Uzbekistan",
        "Aircraft registered in Mali",
        "Architectural elements in Germany",
        "Aircraft in Portugal",
        "Aircraft in Sierra Leone",
        "Aircraft in Malawi",
        "Aircraft in Tanzanian service",
        "Aircraft in Thailand",
    ]


def test_can_find_rare_categories(wikimedia_api: WikimediaApi) -> None:
    result = wikimedia_api.find_matching_categories(query="Aircraft in Taj")

    assert result == [
        "Aircraft in Tajikistan",
        "Aircraft in Tajikistani service",
        "Aircraft in Tajikistani service by airline",
    ]


def test_returns_an_empty_list_if_no_matching_categories(
    wikimedia_api: WikimediaApi,
) -> None:
    assert wikimedia_api.find_matching_categories(query="sdfdsgd") == []
