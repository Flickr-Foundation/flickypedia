from datetime import datetime

from ..types import (
    NewStatement,
    QualifierValues,
    create_qualifiers,
    to_wikidata_entity_value,
)
from ..wikidata_entities import WikidataEntities
from ..wikidata_properties import WikidataProperties


def create_source_statement(
    photo_id: str,
    photo_url: str,
    original_url: str | None,
    retrieved_at: datetime | None,
) -> NewStatement:
    """
    Create a structured data statement for the "source" statement.
    """
    qualifier_values: list[QualifierValues] = [
        {
            "property": WikidataProperties.DescribedAtUrl,
            "value": photo_url,
            "type": "string",
        },
        {
            "property": WikidataProperties.Operator,
            "entity_id": WikidataEntities.Flickr,
            "type": "entity",
        },
    ]

    if original_url is not None:
        qualifier_values.append(
            {
                "property": WikidataProperties.Url,
                "value": original_url,
                "type": "string",
            }
        )

    qualifiers_order = [
        WikidataProperties.DescribedAtUrl,
        WikidataProperties.Operator,
    ]

    if original_url is not None:
        qualifiers_order.append(WikidataProperties.Url)

    if retrieved_at is not None:
        qualifier_values.append(
            {
                "property": WikidataProperties.Retrieved,
                "date": retrieved_at,
                "precision": "day",
                "type": "date",
            }
        )

        qualifiers_order.append(WikidataProperties.Retrieved)

    return {
        "mainsnak": {
            "snaktype": "value",
            "property": WikidataProperties.SourceOfFile,
            "datavalue": to_wikidata_entity_value(
                entity_id=WikidataEntities.FileAvailableOnInternet
            ),
        },
        "qualifiers": create_qualifiers(qualifier_values),
        "qualifiers-order": qualifiers_order,
        "type": "statement",
    }
