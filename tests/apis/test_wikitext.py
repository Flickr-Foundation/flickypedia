import pathlib

import pytest

from flickypedia.apis.wikitext import create_wikitext
from flickypedia.uploadr.config import create_config


def test_create_wikitext_for_photo() -> None:
    actual = create_wikitext(license_id="cc-by-2.0")
    expected = """=={{int:filedesc}}==
{{Information}}

=={{int:license-header}}==
{{Cc-by-2.0}}"""

    assert actual == expected


config = create_config(data_directory=pathlib.Path("data"))


@pytest.mark.parametrize("license_id", config["ALLOWED_LICENSES"])
def test_can_create_wikitext_for_all_allowed_licenses(license_id: str) -> None:
    create_wikitext(license_id=license_id)
