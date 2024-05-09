import typing

from flickypedia.apis.structured_data.wikidata import WikidataProperties as WP
from flickypedia.types.structured_data import (
    BaseStatement,
    ExistingClaims,
    NewClaims,
    NewStatement,
)
from .comparisons import (
    are_equivalent_qualifiers,
    are_equivalent_snaks,
    are_equivalent_statements,
    has_subset_of_new_qualifiers,
)


class DoNothing(typing.TypedDict):
    property_id: str
    action: typing.Literal["do_nothing"]


class AddMissing(typing.TypedDict):
    property_id: str
    action: typing.Literal["add_missing"]
    statement: NewStatement


class AddQualifiers(typing.TypedDict):
    property_id: str
    action: typing.Literal["add_qualifiers"]
    statement_id: str
    statement: NewStatement


class ReplaceStatement(typing.TypedDict):
    property_id: str
    action: typing.Literal["replace_statement"]
    statement_id: str
    statement: NewStatement


class Unknown(typing.TypedDict):
    property_id: str
    action: typing.Literal["unknown"]


Action = DoNothing | AddMissing | AddQualifiers | ReplaceStatement | Unknown


def create_actions(existing_sdc: ExistingClaims, new_sdc: NewClaims) -> list[Action]:
    actions: list[Action] = []

    for new_statement in new_sdc["claims"]:
        property_id = new_statement["mainsnak"]["property"]
        existing_statements = existing_sdc.get(property_id, [])

        # If there are no statements with this property on the
        # existing SDC, then we just need to add it.
        #
        # What if license has changed?
        if not existing_statements and property_id != WP.CopyrightLicense:
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
            if property_id == WP.Creator:
                null_statement: NewStatement = {
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
            # There are some cases where the user property has been populated,
            # but it uses the numeric form of the ID in the URL, rather than
            # the pathalias.  For example, compare:
            #
            #     https://www.flickr.com/people/126377022@N07
            #     https://www.flickr.com/people/internetarchivebookimages/
            #
            # Or maybe there's a "role" qualifier ("object has role: photographer").
            #
            # For now at least, we just care about the user ID being the same; other
            # qualifiers being different are less important to us.
            if (
                property_id == WP.Creator
                and "qualifiers" in statement
                and WP.FlickrUserId in statement["qualifiers"]
                and are_equivalent_snaks(statement["mainsnak"], new_statement["mainsnak"])
                and are_equivalent_qualifiers(
                    existing_qualifiers={
                        WP.FlickrUserId: statement["qualifiers"][WP.FlickrUserId],
                    },
                    new_qualifiers={
                        WP.FlickrUserId: new_statement["qualifiers"][WP.FlickrUserId],
                    },
                )
            ):
                actions.append(DoNothing(property_id=property_id, action="do_nothing"))
                break
            # fmt: on

            # fmt: off
            # There are some cases where the creator is populated with the
            # Flickr username, prefixed with "Flickr user $username".
            #
            # In this case, we can go ahead and replace the existing statement.
            # fmt: on
            if (
                property_id == WP.Creator
                and "qualifiers" in statement
                and are_equivalent_snaks(
                    statement["mainsnak"], new_statement["mainsnak"]
                )
                and statement["qualifiers-order"] == [WP.AuthorName]
                and len(statement["qualifiers"][WP.AuthorName]) == 1
            ):
                old_author_name = get_author_name(statement)
                new_author_name = get_author_name(new_statement)

                if old_author_name in {
                    f"flickr user {new_author_name}",
                    f"Flickr User {new_author_name}",
                    f"Flickr user {new_author_name}",
                    new_author_name,
                }:
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


def get_author_name(statement: BaseStatement) -> str:
    """
    Given a statement, get the string value from the Author Name qualifier.
    """
    value = statement["qualifiers"][WP.AuthorName][0]["datavalue"]["value"]
    assert isinstance(value, str)
    return value
