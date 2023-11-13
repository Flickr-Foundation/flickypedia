import json

import pytest

from flickypedia.apis._types import ExistingClaims, Snak
from flickypedia.utils import validate_typeddict


def test_snak_type_matches() -> None:
    data = {
        "snaktype": "value",
        "property": "P1684",
        "hash": "e9d3441f2099aec262278049bb9915eaf3fc20fb",
        "datavalue": {
            "value": {"text": "910", "language": "en"},
            "type": "monolingualtext",
        },
    }

    validate_typeddict(data, model=Snak)


@pytest.mark.parametrize(
    "filename",
    [
        "M76_P1071_entityid.json",
        "M76_P1259_globecoordinate.json",
        "M76_P6790_quantity.json",
        "M74469_P180_monolingualtext.json",
    ],
)
def test_existing_claims_match_type(filename: str) -> None:
    with open(f"tests/fixtures/structured_data/existing/{filename}") as infile:
        existing_statements = json.load(infile)

    validate_typeddict(existing_statements, model=ExistingClaims)
