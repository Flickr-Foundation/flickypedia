import typing

from flickr_photos_api import DateTaken

from ..types import (
    NewStatement,
    QualifierValues,
    create_qualifiers,
    to_wikidata_date_value,
)
from ..wikidata_entities import WikidataEntities
from ..wikidata_properties import WikidataProperties


def create_date_taken_statement(date_taken: DateTaken) -> NewStatement:
    """
    Create a structured data statement for date taken.

    In most cases this is a single value with a precision attached, but
    for dates which are marked as "circa" on Flickr, we add an additional
    "circa" qualifier.

    Here ``granularity`` comes from the Flickr API: see "Photo Dates".
    https://www.flickr.com/services/api/misc.dates.html
    """
    flickr_granularity = date_taken["granularity"]

    precision_lookup: dict[str, typing.Literal["day", "month", "year"]] = {
        "second": "day",
        "month": "month",
        "year": "year",
        "circa": "year",
    }

    try:
        wikidata_precision = precision_lookup[flickr_granularity]
    except KeyError:
        raise ValueError(f"Unrecognised taken_granularity: {flickr_granularity!r}")

    if flickr_granularity in {"second", "month", "year"}:
        return {
            "mainsnak": {
                "datavalue": to_wikidata_date_value(
                    date_taken["value"], precision=wikidata_precision
                ),
                "property": WikidataProperties.Inception,
                "snaktype": "value",
            },
            "type": "statement",
        }
    else:
        assert flickr_granularity == "circa"

        qualifier_values: list[QualifierValues] = [
            {
                "property": WikidataProperties.SourcingCircumstances,
                "entity_id": WikidataEntities.Circa,
                "type": "entity",
            },
        ]

        return {
            "mainsnak": {
                "datavalue": to_wikidata_date_value(
                    date_taken["value"], precision=wikidata_precision
                ),
                "property": WikidataProperties.Inception,
                "snaktype": "value",
            },
            "qualifiers": create_qualifiers(qualifier_values),
            "qualifiers-order": [WikidataProperties.SourcingCircumstances],
            "type": "statement",
        }
