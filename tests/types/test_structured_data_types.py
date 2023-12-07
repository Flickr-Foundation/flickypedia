import json

import pytest

from flickypedia.types import validate_typeddict
from flickypedia.types.structured_data import ExistingClaims, Snak


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

    validate_typeddict(data, model=ExistingSnak)


@pytest.mark.parametrize(
    "filename",
    [
        # M76 = Bustaxi.jpg
        # Retrieved 7 December 2023
        "M76_P1071_entityid.json",
        "M76_P1259_globecoordinate.json",
        "M76_P6790_quantity.json",
        #
        # M74469 = De Havilland Canada DHC-1 Chipmunk (WB671).jpg
        # Retrieved 7 December 2023
        "M74469_P180_monolingualtext.json",
        #
        # M68208 = Turner, J. M. W. - The Grand Canal - Venice.jpg
        # Retrieved 7 December 2023
        "M68208_P180_references.json",
    ],
)
def test_existing_claims_match_type(filename: str) -> None:
    with open(f"tests/fixtures/structured_data/existing/{filename}") as infile:
        existing_statements = json.load(infile)

    validate_typeddict(existing_statements, model=ExistingClaims)
