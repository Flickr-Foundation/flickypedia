from flask import Flask
import pytest

from flickypedia.structured_data.statements import create_license_statement
from utils import get_statement_fixture


@pytest.mark.parametrize(
    ["license_id", "filename"],
    [
        ("cc-by-2.0", "license_cc_by_2.0.json"),
        ("usgov", "license_usgov.json"),
        ("cc0-1.0", "license_cc0.json"),
    ],
)
def test_create_license_statement(license_id: str, filename: str) -> None:
    actual = create_license_statement(license_id)
    expected = get_statement_fixture(filename)

    assert actual == expected


def test_can_create_license_statement_for_all_allowed_licenses(app: Flask) -> None:
    for license_id in app.config["ALLOWED_LICENSES"]:
        create_license_statement(license_id)


def test_create_license_statement_fails_if_unrecognised_license() -> None:
    with pytest.raises(ValueError, match="Unrecognised license ID"):
        create_license_statement(license_id="mystery")
