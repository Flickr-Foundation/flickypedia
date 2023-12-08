from flickypedia.types.structured_data import ExistingStatement, NewStatement, Snak


def are_equivalent_snaks(existing_snak: Snak, new_snak: Snak) -> bool:
    if existing_snak["property"] != new_snak["property"]:
        return False

    if existing_snak["snaktype"] != new_snak["snaktype"]:
        return False

    existing_datavalue = existing_snak["datavalue"]
    new_datavalue = new_snak["datavalue"]

    if existing_datavalue["type"] != new_datavalue["type"]:
        return False

    if existing_datavalue["type"] == "globecoordinate":
        assert new_datavalue["type"] == "globecoordinate"

        existing_value = existing_datavalue["value"]
        new_value = new_datavalue["value"]

        return (
            new_value["altitude"] == existing_value["altitude"]
            and new_value["globe"] == existing_value["globe"]
            and new_value["latitude"] == existing_value["latitude"]
            and new_value["longitude"] == existing_value["longitude"]
        )
    else:
        return new_datavalue == existing_datavalue


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

    # If they're globe coordinates, we want to check that the key values
    # are correct, but we'll allow some fudging on the precision -- that's
    # a bit inexact and I'm not too fussed about it.
    if has_no_qualifiers and are_equivalent_snaks(
        existing_snak=existing_statement["mainsnak"], new_snak=new_statement["mainsnak"]
    ):
        return True

    return False
