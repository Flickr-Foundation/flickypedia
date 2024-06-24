from ..types import NewStatement, to_wikidata_entity_value
from ..wikidata_entities import WikidataEntities
from ..wikidata_properties import WikidataProperties


def create_license_statement(license_id: str) -> NewStatement:
    """
    Create a structured data statement for copyright license.
    """
    try:
        wikidata_license_id = WikidataEntities.Licenses[license_id]
    except KeyError:
        raise ValueError(f"Unrecognised license ID: {license_id!r}")

    return {
        "mainsnak": {
            "snaktype": "value",
            "property": WikidataProperties.CopyrightLicense,
            "datavalue": to_wikidata_entity_value(entity_id=wikidata_license_id),
        },
        "type": "statement",
    }
