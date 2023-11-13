"""
Definitions for Wikidata structured data entities.

We don't do any validation beyond the structure of the types --
this allows us to write type-checked Python, which makes it much
easier to write certain operations.

e.g. we can compare two snaks (one we want to write, one that exists)
and be sure we know what fields are/aren't defined, rather than
writing overly defensive code at every step.

These types aren't as strict as Wikidata itself, but we're not
trying to replace Wikidata validation, just allow ourselves to
write sensible validation logic.
"""

from typing import Dict, List, Literal, TypedDict, Union


# Definitions for the Wikidata entities that we create as part of
# this library for new photos.
#
# Notable, these entities omit a couple of fields on the main entities,
# in particular rank and ID.
#
# This is based on the table structured as described in
# https://www.wikidata.org/wiki/Help:Wikidata_datamodel


# -> datavalue
#
#     -> type: wikibase-entityid
#        value:
#          entity type: item
#          numeric-id
#
#     -> type: string
#        value (string/image/url)
#
#     -> type: time
#        value
#          time
#          precision
#          before
#          after
#          timezone
#          calendarmodel
#
#     -> type: globecoordinate
#          latitude
#          longitude
#          precision
#          globe
#          altitude (not documented but present in data model)
#
#     -> type: quantity
#          amount
#          lowerBound (not yet seen in responses)
#          upperBound (not yet seen in responses)
#          unit
#
#     -> type: monolingualtext
#          text
#          language
#
class Value:
    WikibaseEntityId = TypedDict(
        "WikibaseEntityId",
        {"entity-type": Literal["item"], "id": str, "numeric-id": int},
    )
    Time = TypedDict(
        "Time",
        {
            "time": str,
            "precision": int,
            "before": int,
            "after": int,
            "timezone": int,
            "calendarmodel": str,
        },
    )
    GlobeCoordinate = TypedDict(
        "GlobeCoordinate",
        {
            "latitude": float,
            "longitude": float,
            "precision": float,
            "globe": str,
            "altitude": Literal[None],
        },
    )
    Quantity = TypedDict("Quantity", {"amount": str, "unit": str})
    MonolingualText = TypedDict("MonolingualText", {"text": str, "language": str})


class DataValueTypes:
    WikibaseEntityId = TypedDict(
        "WikibaseEntityId",
        {"type": Literal["wikibase-entityid"], "value": Value.WikibaseEntityId},
    )
    String = TypedDict("String", {"type": Literal["string"], "value": str})
    Time = TypedDict("Time", {"type": Literal["time"], "value": Value.Time})
    GlobeCoordinate = TypedDict(
        "GlobeCoordinate",
        {"type": Literal["globecoordinate"], "value": Value.GlobeCoordinate},
    )
    Quantity = TypedDict(
        "Quantity", {"type": Literal["quantity"], "value": Value.Quantity}
    )
    MonolingualText = TypedDict(
        "MonolingualText",
        {"type": Literal["monolingualtext"], "value": Value.MonolingualText},
    )


DataValue = Union[
    DataValueTypes.WikibaseEntityId,
    DataValueTypes.String,
    DataValueTypes.Time,
    DataValueTypes.GlobeCoordinate,
    DataValueTypes.Quantity,
    DataValueTypes.MonolingualText,
]


class SnakTypes:
    Value = TypedDict(
        "Value", {"snaktype": Literal["value"], "property": str, "datavalue": DataValue}
    )
    SomeValue = TypedDict(
        "SomeValue", {"snaktype": Literal["somevalue"], "property": str}
    )


Snak = Union[SnakTypes.Value, SnakTypes.SomeValue]


class StatementTypes:
    UnqualifiedStatement = TypedDict(
        "UnqualifiedStatement",
        {"mainsnak": Snak, "type": Literal["statement"]},
    )

    QualifiedStatement = TypedDict(
        "QualifiedStatement",
        {
            "mainsnak": Snak,
            "qualifiers": Dict[str, List[Snak]],
            "qualifiers-order": List[str],
            "type": Literal["statement"],
        },
    )


Statement = Union[
    StatementTypes.UnqualifiedStatement, StatementTypes.QualifiedStatement
]


class StructuredDataClaims(TypedDict):
    claims: List[Statement]


class TitleValidationResult:
    Ok = TypedDict("Ok", {"result": Literal["ok"]})
    Failed = TypedDict(
        "Failed",
        {
            "result": Literal["blacklisted", "duplicate", "invalid", "too_long"],
            "text": str,
        },
    )


TitleValidation = Union[TitleValidationResult.Ok, TitleValidationResult.Failed]
