from flickr_url_parser import (
    parse_flickr_url,
    NotAFlickrUrl,
    ParseResult,
    UnrecognisedUrl,
)

from .wikidata import WikidataEntities, WikidataProperties, to_wikidata_entity_value
from flickypedia.types.structured_data import ExistingClaims, ExistingStatement, Snak


def get_single_qualifier(
    statement: ExistingStatement, *, property_id: str
) -> Snak | None:
    """
    A statement can have qualifiers:

        statement: {
            qualifiers: Qualifiers
            ...
        }

    In most cases, there's exactly one Snak per property ID, e.g.

        statement: {
            qualifiers: {
                P123: [Snak],
                P456: [Snak],
            }
        }

    This function looks for exactly one Snak in a property, and returns
    it if found.

    If there are no Snaks (this property isn't used as a qualifier) or
    there are multiple Snaks for a property, it returns ``None``.
    """
    qualifiers = statement.get("qualifiers", {})

    snak_list = qualifiers.get(property_id, [])

    if len(snak_list) == 0:
        return None

    if len(snak_list) != 1:
        raise AmbiguousStructuredData(
            f"Unexpected multiple qualifiers in {statement['id']}"
        )

    return snak_list[0]


class AmbiguousStructuredData(Exception):
    pass


def find_flickr_urls_in_sdc(sdc: ExistingClaims) -> list[tuple[str, ParseResult]]:
    """
    Return a list of Flickr URLs which were found in the SDC.

    These are guaranteed to be parseable using flickr-url-parser.
    """
    result: list[tuple[str, ParseResult]] = []

    # Look for URLs in the "Source" field, which might point to
    # a Flickr photo.
    for statement in sdc.get(WikidataProperties.SourceOfFile, []):
        # First check if the Operator is "Flickr".  If it's not, this
        # isn't a Flickr source and we can skip it.
        operator = get_single_qualifier(
            statement, property_id=WikidataProperties.Operator
        )

        flickr = to_wikidata_entity_value(entity_id=WikidataEntities.Flickr)

        if operator is not None and operator["datavalue"] != flickr:
            continue

        # Now look at the "URL" and "Published at" qualifiers.  Either of
        # them could contain a Flickr URL.
        url = get_single_qualifier(statement, property_id=WikidataProperties.Url)
        published_at = get_single_qualifier(
            statement, property_id=WikidataProperties.DescribedAtUrl
        )

        for u in (url, published_at):
            if u is None:
                continue

            if u["datavalue"]["type"] != "string":
                continue

            value = u["datavalue"]["value"]

            try:
                parsed_url = parse_flickr_url(value)
            except (UnrecognisedUrl, NotAFlickrUrl):
                pass
            else:
                result.append((value, parsed_url))

    return result
