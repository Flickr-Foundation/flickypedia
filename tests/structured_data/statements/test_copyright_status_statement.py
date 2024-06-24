import pytest

from flickypedia.structured_data.statements import create_copyright_status_statement
from utils import get_statement_fixture


def test_create_copyright_status_statement_fails_for_unknown_license() -> None:
    with pytest.raises(ValueError, match="Unable to map a copyright status"):
        create_copyright_status_statement(license_id="cc-by-nc-2.0")


@pytest.mark.parametrize(
    ["license_id", "filename"],
    [
        ("cc-by-2.0", "copyright_status_copyrighted.json"),
        ("cc-by-sa-2.0", "copyright_status_copyrighted.json"),
        ("usgov", "copyright_status_usgov.json"),
        ("cc0-1.0", "copyright_status_public_domain.json"),
        ("pdm", "copyright_status_public_domain.json"),
    ],
)
def test_create_copyright_status_statement(license_id: str, filename: str) -> None:
    result = create_copyright_status_statement(license_id=license_id)
    expected = get_statement_fixture(filename)

    assert result == expected
