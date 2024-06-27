import re

from flickr_url_parser import parse_flickr_url

from flickypedia.structured_data import (
    ExistingStatement,
    NewStatement,
    Qualifiers,
    Snak,
    Value,
    WikidataDatePrecision,
    WikidataProperties,
)


def are_equivalent_flickr_urls(url1: str, url2: str) -> bool:
    """
    Returns True if two URLs point to equivalent pages on Flickr,
    False otherwise.
    """
    try:
        parsed_url_1 = parse_flickr_url(url1)
        parsed_url_2 = parse_flickr_url(url2)
    except Exception:
        return False

    # Compare the two Flickr URLs, but we apply a slightly stricter check:
    # we only want single photos to match if they point at the same
    # *description* page, not the raw JPEG.
    #
    # So two variants of a photo page are equivalent, but a photo page and
    # JPEG aren't equivalet.
    #
    # See the tests for examples.
    if (
        parsed_url_1["type"] == "single_photo"
        and parsed_url_2["type"] == "single_photo"
        and parsed_url_1["photo_id"] == parsed_url_2["photo_id"]
        and (parsed_url_1["user_id"] or parsed_url_1["user_url"])
        and (parsed_url_2["user_id"] or parsed_url_2["user_url"])
    ):
        return True

    return parsed_url_1 == parsed_url_2


def are_equivalent_times(time1: Value.Time, time2: Value.Time) -> bool:
    """
    Compare two time values.

    Note that we allow a certain amount of slop based on the precision,
    e.g. if you're using year-level precision, then 2001-00-00 and 2001-01-01
    are equivalent.
    """
    for key in ("precision", "before", "after", "timezone", "calendarmodel"):
        if time1[key] != time2[key]:  # type: ignore
            return False

    # e.g. +1896-01-01T00:00:00Z
    time_format = re.compile(
        r"^\+[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
    )

    value1 = time1["time"]
    value2 = time2["time"]

    if not time_format.match(value1) or not time_format.match(value2):
        return False

    if time1["precision"] == WikidataDatePrecision.Year:
        return value1[: len("+1896")] == value2[: len("+1896")]
    elif time1["precision"] == WikidataDatePrecision.Month:
        return value1[: len("+1896-01")] == value2[: len("+1896-01")]
    elif time1["precision"] == WikidataDatePrecision.Day:
        return value1[: len("+1896-01-02")] == value2[: len("+1896-01-02")]

    # We only write day/month/year statements in our code, so we should
    # never get here in practice, but we include it defensively.
    else:  # pragma: no cover
        raise ValueError(f'Unrecognised precision: {time1["precision"]}')


def are_equivalent_snaks(existing_snak: Snak, new_snak: Snak) -> bool:
    if existing_snak["property"] != new_snak["property"]:
        return False

    if existing_snak["snaktype"] != new_snak["snaktype"]:
        return False

    # If they have the same property and snaktype, and those are the
    # only two fields, then these snaks are equivalent.
    if existing_snak.keys() == {"property", "snaktype", "hash"} and new_snak.keys() == {
        "property",
        "snaktype",
    }:
        return True

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

    # If we're looking at the "Described At URL" field and they have two
    # equivalent Flickr URLs, we can treat these as equivalent.
    elif (
        existing_datavalue["type"] == "string"
        and new_datavalue["type"] == "string"
        and existing_snak["property"] == WikidataProperties.DescribedAtUrl
    ):
        return are_equivalent_flickr_urls(
            existing_datavalue["value"], new_datavalue["value"]
        )

    # If we're looking at the "URL" field and they have two
    # equivalent Flickr URLs, we can treat these as equivalent.
    elif (
        existing_datavalue["type"] == "string"
        and new_datavalue["type"] == "string"
        and existing_snak["property"] == WikidataProperties.Url
    ):
        return are_equivalent_flickr_urls(
            existing_datavalue["value"], new_datavalue["value"]
        )

    elif existing_datavalue["type"] == "time" and new_datavalue["type"] == "time":
        return are_equivalent_times(
            time1=existing_datavalue["value"], time2=new_datavalue["value"]
        )

    else:
        return new_datavalue == existing_datavalue


def are_equivalent_qualifiers(
    existing_qualifiers: Qualifiers, new_qualifiers: Qualifiers
) -> bool:
    # If we're not trying to write any qualifiers, then any existing
    # qualifiers are trivially equivalent.
    if not new_qualifiers:
        return True

    for property_id, list_of_snaks in new_qualifiers.items():
        assert len(list_of_snaks) == 1
        new_snak = list_of_snaks[0]

        if not any(
            are_equivalent_snaks(snak, new_snak)
            for snak in existing_qualifiers.get(property_id, [])
        ):
            return False

    return True


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

    main_snaks_match = are_equivalent_snaks(
        existing_snak=existing_statement["mainsnak"], new_snak=new_statement["mainsnak"]
    )

    qualifiers_match = are_equivalent_qualifiers(
        existing_qualifiers=existing_statement.get("qualifiers", {}),
        new_qualifiers=new_statement.get("qualifiers", {}),
    )

    return qualifiers_match and main_snaks_match


def has_subset_of_new_qualifiers(
    existing_statement: ExistingStatement, new_statement: NewStatement
) -> bool:
    """
    Returns True if the existing statement has all the qualifiers of the
    new statement.

    There are some cases where the file on Wikimedia Commons has more
    qualifiers than we use; we don't care about their value and just want
    to compare the values of the qualifiers we set.
    """
    existing_qualifiers = existing_statement.get("qualifiers", {})

    for property_id, existing_qualifier_list in existing_qualifiers.items():
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
