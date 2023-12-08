from flickypedia.types.structured_data import ExistingStatement, NewStatement


def are_equivalent_statements(
    existing_statement: ExistingStatement, new_statement: NewStatement
) -> bool:
    """
    Returns True if these two statements are equivalent.

    In practical terms, if two statements are equivalent, that means we
    definitely don't need to update the statement in Wikimedia Commons.

    If the two statements aren't equivalent, then we **might** need to do
    something, but what we do is beyond the scope of this function.
    """
    has_no_qualifiers = (
        "qualifiers" not in existing_statement and "qualifiers" not in new_statement
    )

    # First check the type of the datavalue -- if it's not the same, these
    # definitely can't be equivalent statements.
    has_same_datavalue_type = (
        new_statement["mainsnak"]["datavalue"]["type"]
        == existing_statement["mainsnak"]["datavalue"]["type"]
    )

    if not has_same_datavalue_type:
        return False

    datavalue_type = new_statement["mainsnak"]["datavalue"]["type"]

    # If they're globe coordinates, we want to check that the key values
    # are correct, but we'll allow some fudging on the precision -- that's
    # a bit inexact and I'm not too fussed about it.
    if datavalue_type == "globecoordinate" and has_no_qualifiers:
        new_value = new_statement["mainsnak"]["datavalue"]["value"]
        existing_value = existing_statement["mainsnak"]["datavalue"]["value"]

        if all(
            new_value[k] == existing_value[k]
            for k in {"altitude", "globe", "latitude", "longitude"}
        ):
            return True
        else:
            return False

    return False
