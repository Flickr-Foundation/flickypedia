import copy
from typing import Literal, TypedDict

from flickypedia.types.structured_data import (
    ExistingClaims,
    ExistingStatement,
    NewClaims,
    NewStatement,
)


class DoNothing(TypedDict):
    property_id: str
    action: Literal["do_nothing"]


class AddMissing(TypedDict):
    property_id: str
    action: Literal["add_missing"]
    statement: NewStatement


class AddQualifiers(TypedDict):
    property_id: str
    action: Literal["add_qualifiers"]
    statement_id: str
    statement: NewStatement


class Unknown(TypedDict):
    property_id: str
    action: Literal["unknown"]


Action = DoNothing | AddMissing | AddQualifiers


def normalise(statement: ExistingStatement) -> NewStatement:
    normalised_statement = copy.deepcopy(statement)

    del normalised_statement["id"]
    del normalised_statement["rank"]

    del normalised_statement["mainsnak"]["hash"]

    for qualifiers in normalised_statement.get("qualifiers", {}).values():
        for q in qualifiers:
            del q["hash"]

    return normalised_statement


def create_actions(existing_sdc: ExistingClaims, new_sdc: NewClaims) -> list[Action]:
    actions: list[Action] = []

    for new_statement in new_sdc["claims"]:
        property_id = new_statement["mainsnak"]["property"]
        existing_statements = existing_sdc.get(property_id, [])

        # If there are no statements with this property on the
        # existing SDC, then we just need to add it.
        if not existing_statements:
            actions.append(
                AddMissing(
                    property_id=property_id,
                    action="add_missing",
                    statement=new_statement,
                )
            )
            continue

        for statement in existing_statements:
            normalised_statement = normalise(statement)

            # If there's an equivalent statement in the existing SDC,
            # then we don't need to do anything.
            if normalised_statement == new_statement:
                actions.append(DoNothing(property_id=property_id, action="do_nothing"))
                break

            # If the existing statement has the same mainsnak and a subset
            # of the qualifiers, then we need to update it.
            has_same_mainsnak = (
                normalised_statement["mainsnak"] == new_statement["mainsnak"]
            )

            has_subset_of_new_qualifiers = all(
                new_statement["qualifiers"].get(q)
                == normalised_statement["qualifiers"][q]
                for q in normalised_statement["qualifiers"]
            )

            if has_same_mainsnak and has_subset_of_new_qualifiers:
                actions.append(
                    AddQualifiers(
                        property_id=property_id,
                        action="add_qualifiers",
                        statement_id=statement["id"],
                        statement=new_statement,
                    )
                )
                break
        else:  # no break
            actions.append(Unknown(property_id=property_id, action="unknown"))

    return actions
