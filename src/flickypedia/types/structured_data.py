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

import typing


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
    WikibaseEntityId = typing.TypedDict(
        "WikibaseEntityId",
        {"entity-type": typing.Literal["item"], "id": str, "numeric-id": int},
    )
    Time = typing.TypedDict(
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
    GlobeCoordinate = typing.TypedDict(
        "GlobeCoordinate",
        {
            "latitude": float,
            "longitude": float,
            "precision": float,
            "globe": str,
            "altitude": typing.Literal[None],
        },
    )
    Quantity = typing.TypedDict("Quantity", {"amount": str, "unit": str})
    MonolingualText = typing.TypedDict(
        "MonolingualText", {"text": str, "language": str}
    )


class DataValueTypes:
    WikibaseEntityId = typing.TypedDict(
        "WikibaseEntityId",
        {"type": typing.Literal["wikibase-entityid"], "value": Value.WikibaseEntityId},
    )
    String = typing.TypedDict(
        "String", {"type": typing.Literal["string"], "value": str}
    )
    Time = typing.TypedDict(
        "Time", {"type": typing.Literal["time"], "value": Value.Time}
    )
    GlobeCoordinate = typing.TypedDict(
        "GlobeCoordinate",
        {"type": typing.Literal["globecoordinate"], "value": Value.GlobeCoordinate},
    )
    Quantity = typing.TypedDict(
        "Quantity", {"type": typing.Literal["quantity"], "value": Value.Quantity}
    )
    MonolingualText = typing.TypedDict(
        "MonolingualText",
        {"type": typing.Literal["monolingualtext"], "value": Value.MonolingualText},
    )


DataValue = (
    DataValueTypes.WikibaseEntityId
    | DataValueTypes.String
    | DataValueTypes.Time
    | DataValueTypes.GlobeCoordinate
    | DataValueTypes.Quantity
    | DataValueTypes.MonolingualText
)


# -> snak
#
#    -> property: pxx
#    -> snaktype: value / somevalue / novalue
#    -> (datavalue) ->
#
class Snak(typing.TypedDict):
    property: str
    snaktype: typing.Literal["value", "somevalue", "novalue"]
    datavalue: typing.NotRequired[DataValue]
    hash: typing.NotRequired[str]


# -> references
#
#   hash
#   snaks-order
#     0..*
#       pxx
#   snaks
#     pxx
#       0..*
#         -> snak
#
NewReference = typing.TypedDict(
    "NewReference", {"snaks-order": list[str], "snaks": dict[str, list[Snak]]}
)

ExistingReference = typing.TypedDict(
    "ExistingReference",
    {"hash": str, "snaks-order": list[str], "snaks": dict[str, list[Snak]]},
)


# -> claims
#
# pxx
#   0..*
#     id
#     rank
#     type = statement
#     mainsnak -> snak
#     (qualifiers-order)
#     (qualifiers)
#     (references)
#
Qualifiers = dict[str, list[Snak]]

BaseStatement = typing.TypedDict(
    "BaseStatement",
    {
        "type": typing.Literal["statement"],
        "mainsnak": Snak,
        "qualifiers-order": typing.NotRequired[list[str]],
        "qualifiers": typing.NotRequired[Qualifiers],
    },
)


class NewStatement(BaseStatement):
    references: typing.NotRequired[list[NewReference]]
    id: typing.NotRequired[str]


class ExistingStatement(BaseStatement):
    references: typing.NotRequired[list[ExistingReference]]
    id: str
    rank: typing.Literal["deprecated", "normal", "preferred"]


class NewClaims(typing.TypedDict):
    claims: list[NewStatement]


ExistingClaims = dict[str, list[ExistingStatement]]
