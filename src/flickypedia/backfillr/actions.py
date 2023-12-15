from typing import Literal, TypedDict

from flickypedia.apis.structured_data.wikidata import WikidataProperties
from flickypedia.types.structured_data import (
    ExistingClaims,
    ExistingStatement,
    NewClaims,
    NewStatement,
)
from .comparisons import are_equivalent_qualifiers, are_equivalent_snaks, are_equivalent_statements


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


class ReplaceStatement(TypedDict):
    property_id: str
    action: Literal["replace_statement"]
    statement_id: str
    statement: NewStatement


class Unknown(TypedDict):
    property_id: str
    action: Literal["unknown"]


Action = DoNothing | AddMissing | AddQualifiers | ReplaceStatement | Unknown


def has_subset_of_new_qualifiers(
    existing_statement: ExistingStatement, new_statement: NewStatement
) -> bool:
    for property_id, existing_qualifier_list in existing_statement.get(
        "qualifiers", {}
    ).items():
        try:
            new_qualifier_list = new_statement["qualifiers"][property_id]
            assert len(new_qualifier_list) == 1
            new_qualifier = new_qualifier_list[0]
        except KeyError:
            return False

        if not any(
            are_equivalent_snaks(existing_qualifier, new_qualifier)
            for existing_qualifier in existing_qualifier_list
        ):
            return False

    return True


def create_actions(existing_sdc: ExistingClaims, new_sdc: NewClaims) -> list[Action]:
    actions: list[Action] = []

    for new_statement in new_sdc["claims"]:
        property_id = new_statement["mainsnak"]["property"]
        existing_statements = existing_sdc.get(property_id, [])

        # If there are no statements with this property on the
        # existing SDC, then we just need to add it.
        #
        # What if license has changed?
        if (
            not existing_statements
            and property_id != WikidataProperties.CopyrightLicense
        ):
            actions.append(
                AddMissing(
                    property_id=property_id,
                    action="add_missing",
                    statement=new_statement,
                )
            )
            continue

        for statement in existing_statements:
            # If there's an equivalent statement in the existing SDC,
            # then we don't need to do anything.
            if are_equivalent_statements(statement, new_statement):
                actions.append(DoNothing(property_id=property_id, action="do_nothing"))
                break

            # I've noticed a number of files where the only statement for
            # "Creator" is the single string "null".
            #
            # This looks like a mistake introduced by another tool; in this
            # case we're happy to overwrite it.
            if property_id == WikidataProperties.Creator:
                print(statement)
                print(new_statement)

                null_statement: ExistingStatement = {
                    "type": "statement",
                    "mainsnak": {
                        "property": "P170",
                        "snaktype": "somevalue",
                    },
                    "qualifiers-order": ["P2093"],
                    "qualifiers": {
                        "P2093": [
                            {
                                "property": "P2093",
                                "snaktype": "value",
                                "datavalue": {"type": "string", "value": "null"},
                            }
                        ]
                    },
                }

                if are_equivalent_statements(statement, null_statement):
                    actions.append(
                        ReplaceStatement(
                            property_id=property_id,
                            action="replace_statement",
                            statement_id=statement["id"],
                            statement=new_statement,
                        )
                    )
                    break

            # fmt: off
            if (
                property_id == WikidataProperties.Creator
                and set(statement["qualifiers-order"]) == set(new_statement["qualifiers-order"])
                and are_equivalent_snaks(statement["mainsnak"], new_statement["mainsnak"])
                and are_equivalent_qualifiers(
                    existing_qualifiers={WikidataProperties.FlickrUserId: statement["qualifiers"][WikidataProperties.FlickrUserId]},
                    new_qualifiers={WikidataProperties.FlickrUserId: new_statement["qualifiers"][WikidataProperties.FlickrUserId]},
                )
            ):
                actions.append(
                    ReplaceStatement(
                        property_id=property_id,
                        action="replace_statement",
                        statement_id=statement["id"],
                        statement=new_statement,
                    )
                )
                break
            # fmt: on

            # If the existing statement has the same mainsnak and a subset
            # of the qualifiers, then we need to update it.
            has_same_mainsnak = are_equivalent_snaks(
                existing_snak=statement["mainsnak"], new_snak=new_statement["mainsnak"]
            )

            if has_same_mainsnak and has_subset_of_new_qualifiers(
                statement, new_statement
            ):
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
