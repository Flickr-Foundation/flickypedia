from ..types import (
    NewStatement,
    QualifierValues,
    create_qualifiers,
    to_wikidata_entity_value,
)
from ..wikidata_entities import WikidataEntities
from ..wikidata_properties import WikidataProperties


def create_copyright_status_statement(license_id: str) -> NewStatement:
    """
    Create a structured data statement for a copyright status.
    """
    if license_id in {"cc-by-2.0", "cc-by-sa-2.0"}:
        return {
            "mainsnak": {
                "snaktype": "value",
                "property": WikidataProperties.CopyrightStatus,
                "datavalue": to_wikidata_entity_value(
                    entity_id=WikidataEntities.Copyrighted
                ),
            },
            "type": "statement",
        }
    elif license_id == "usgov":
        qualifier_values: list[QualifierValues] = [
            {
                "property": WikidataProperties.AppliesToJurisdiction,
                "entity_id": WikidataEntities.UnitedStatesOfAmerica,
                "type": "entity",
            },
            {
                "property": WikidataProperties.DeterminationMethod,
                "entity_id": WikidataEntities.WorkOfTheFederalGovernmentOfTheUnitedStates,
                "type": "entity",
            },
        ]

        return {
            "mainsnak": {
                "snaktype": "value",
                "property": WikidataProperties.CopyrightStatus,
                "datavalue": to_wikidata_entity_value(
                    entity_id=WikidataEntities.PublicDomain
                ),
            },
            "qualifiers": create_qualifiers(qualifier_values),
            "qualifiers-order": [
                WikidataProperties.AppliesToJurisdiction,
                WikidataProperties.DeterminationMethod,
            ],
            "type": "statement",
        }

    # See https://commons.wikimedia.org/wiki/Commons:Structured_data/Modeling/Copyright#Copyrighted,_dedicated_to_the_public_domain_by_copyright_holder
    elif license_id in {"cc0-1.0", "pdm"}:
        return {
            "mainsnak": {
                "snaktype": "value",
                "property": WikidataProperties.CopyrightStatus,
                "datavalue": to_wikidata_entity_value(
                    entity_id=WikidataEntities.DedicatedToPublicDomainByCopyrightOwner
                ),
            },
            "type": "statement",
        }

    # We don't map all licenses in this function -- just the licenses
    # which are accepted on Wikimedia Commons.
    #
    # In theory we should never be creating SDC for photos which can't
    # be shared on WMC; this is to give a helpful error if we do.
    else:
        raise ValueError(f"Unable to map a copyright status for license {license_id!r}")
