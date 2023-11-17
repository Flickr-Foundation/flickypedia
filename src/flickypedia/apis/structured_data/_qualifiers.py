"""
A small DSL for creating qualifier values.

The way you specify qualifiers in the Wikidata model is a little
roundabout and repetitive; we have to create JSON like so:

    "qualifiers": {
        $propertyId: [
            {
                "datavalue": $datavalue,
                "property": $propertyId,
                "snaktype": "value"
            }
        ],
        …
    }

This is mildly annoying because you have to repeat the property ID,
and wrap your value in a single-element list.

This allows us to specify our qualifiers in a less repetitive way:

    [
        {
            "property": $propertyId,
             "datavalue": $datavalue,
             "type": "string|entity|date"
        },
        …
    ]

and then the ``create_qualifiers()`` function transforms them into
the required JSON.

"""

import datetime
from typing import Dict, List, Literal, TypedDict, Union

from ._types import DataValue, Snak
from .wikidata import to_wikidata_date_value, to_wikidata_entity_value


class QualifierValueTypes:
    String = TypedDict(
        "String", {"type": Literal["string"], "property": str, "value": str}
    )
    Entity = TypedDict(
        "Entity", {"type": Literal["entity"], "property": str, "entity_id": str}
    )
    Date = TypedDict(
        "Date",
        {
            "type": Literal["date"],
            "property": str,
            "date": datetime.datetime,
            "precision": str,
        },
    )


QualifierValues = Union[
    QualifierValueTypes.String,
    QualifierValueTypes.Entity,
    QualifierValueTypes.Date,
]


def create_qualifiers(qualifier_values: List[QualifierValues]) -> Dict[str, List[Snak]]:
    result: Dict[str, List[Snak]] = {}

    for qualifier in qualifier_values:
        property_id = qualifier["property"]

        datavalue: DataValue

        if qualifier["type"] == "string":
            datavalue = {"type": "string", "value": qualifier["value"]}
        elif qualifier["type"] == "entity":
            datavalue = to_wikidata_entity_value(entity_id=qualifier["entity_id"])
        else:
            assert qualifier["type"] == "date"
            datavalue = to_wikidata_date_value(
                qualifier["date"], precision=qualifier["precision"]
            )

        result[property_id] = [
            {
                "datavalue": datavalue,
                "property": property_id,
                "snaktype": "value",
            }
        ]

    return result
