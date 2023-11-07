from typing import Dict, List, Literal, TypedDict, Union


class DataTypes:
    class Date(TypedDict):
        time: str
        precision: int
        timezone: int
        before: int
        after: int
        calendarmodel: str

    Identifiable = TypedDict("Identifiable", {"id": str})


class DataValueTypes:
    Time = TypedDict("Time", {"type": Literal["time"], "value": DataTypes.Date})
    String = TypedDict("String", {"type": Literal["string"], "value": str})
    Entity = TypedDict(
        "Entity",
        {"type": Literal["wikibase-entityid"], "value": DataTypes.Identifiable},
    )


DataValue = Union[
    DataValueTypes.Time,
    DataValueTypes.String,
    DataValueTypes.Entity,
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
