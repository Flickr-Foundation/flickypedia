import pytest

from flickypedia.apis import WikimediaApi


@pytest.mark.parametrize(
    ["title", "result"],
    [
        pytest.param(
            "File:StainedGlassWindowAtEly.jpg",
            "duplicate",
            id="duplicate_title",
        ),
        pytest.param("File:P60506151.jpg", "blacklisted", id="blacklisted_title"),
        pytest.param(
            "File:" + "a" * 241 + ".tiff",
            "too_long",
            id="barely_too_long_title",
        ),
        pytest.param(f"File:{'Fishing' * 100}.jpg", "too_long", id="too_long_title"),
        pytest.param(
            "File:{with invalid chars}.jpg",
            "invalid",
            id="disallowed_characters",
        ),
        pytest.param("File:\b\b\b.jpg", "invalid", id="disallowed_characters_2"),
        pytest.param("File:.", "invalid", id="only_a_single_period"),
        pytest.param("File:FishingBoatsByTheRiver.jpg", "ok", id="allowed_title"),
        pytest.param("File:FishingBoatsByTheRiver.jpg", "ok", id="allowed_title"),
    ],
)
def test_validate_title(wikimedia_api: WikimediaApi, title: str, result: str) -> None:
    assert wikimedia_api.validate_title(title=title)["result"] == result


def test_validate_title_links_to_duplicates(wikimedia_api: WikimediaApi) -> None:
    result = wikimedia_api.validate_title(title="File:P1.jpg")

    assert result == {
        "result": "duplicate",
        "text": "Please choose a different title. There is already <a href='https://commons.wikimedia.org/wiki/File:P1.jpg'>a file on Commons</a> with that title.",
    }


def test_validate_title_links_to_normalised_duplicates(
    wikimedia_api: WikimediaApi,
) -> None:
    result = wikimedia_api.validate_title(title="File:Tower Bridge at Night.jpg")

    assert result == {
        "result": "duplicate",
        "text": "Please choose a different title. There is already a file <a href='https://commons.wikimedia.org/wiki/File:Tower Bridge at Night.JPG'>Tower Bridge at Night.JPG</a> on Commons.",
    }


def test_validate_title_links_to_case_insensitive_duplicates(
    wikimedia_api: WikimediaApi,
) -> None:
    result = wikimedia_api.validate_title(title="File:tower bridge at night.jpg")

    assert result == {
        "result": "duplicate",
        "text": "Please choose a different title. There is already a file <a href='https://commons.wikimedia.org/wiki/File:Tower Bridge at Night.JPG'>Tower Bridge at Night.JPG</a> on Commons.",
    }


@pytest.mark.parametrize(
    "title",
    [
        "Belgian President in 2023.jpg",
        "Jam on a slice of bread.png",
        "A shipping container full of bees.JPEG",
    ],
)
def test_validate_title_rejects_image_suffix(
    wikimedia_api: WikimediaApi, title: str
) -> None:
    result = wikimedia_api.validate_title(title=f"File:{title}.jpg")

    assert result == {
        "result": "invalid",
        "text": "Please remove the filename suffix; it will be added automatically.",
    }


@pytest.mark.parametrize(
    "title",
    [
        pytest.param("This:is:a:title:with:colons", id="with_colons"),
        pytest.param("This/is\\a/title\\with/slashes", id="with_slashes"),
    ],
)
def test_validate_title_rejects_illegal_chars(
    wikimedia_api: WikimediaApi, title: str
) -> None:
    result = wikimedia_api.validate_title(title=f"File:{title}.jpg")

    assert result == {
        "result": "invalid",
        "text": "This title is invalid. Make sure to remove characters like square brackets, colons, slashes, comparison operators, pipes and curly brackets.",
    }
