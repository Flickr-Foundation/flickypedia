from flickr_url_parser import parse_flickr_url, NotAFlickrUrl, UnrecognisedUrl

from .wikidata import WikidataEntities, WikidataProperties, to_wikidata_entity_value
from flickypedia.types.structured_data import ExistingClaims, ExistingStatement, Snak


class AmbiguousStructuredData(Exception):
    pass


def get_single_qualifier(
    page_id: str, statement: ExistingStatement, *, property_id: str
) -> Snak | None:
    """
    A statement can have qualifiers:

        statement: {
            qualifiers: dict[str, list[Snak]]
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
        raise AmbiguousStructuredData(f"Unexpected multiple qualifiers on {page_id} / {statement['id']}")

    return snak_list[0]


def find_flickr_photo_id(page_id: str,sdc: ExistingClaims) -> str | None:
    """
    Given the structured data for a file on Wikimedia Commons, guess
    what Flickr photo ID this is associated with (if any).

    Note: there are a bunch of `assert 0`'s littered through this code,
    which are branches I haven't tested because I haven't encountered
    them in practice yet.  If you hit one of these in practice, use it
    as an example to write a test!
    """
    candidates = set()

    # Look for URLs in the "Source" field, which might point to
    # a Flickr photo.
    for statement in sdc.get(WikidataProperties.SourceOfFile, []):
        # First check if the Operator is "Flickr".  If it's not, this
        # isn't a Flickr source and we can skip it.
        operator = get_single_qualifier(
            page_id, statement, property_id=WikidataProperties.Operator
        )

        if operator is None:
            continue

        if operator["datavalue"] != to_wikidata_entity_value(
            entity_id=WikidataEntities.Flickr
        ):
            continue

        # Now look at the "URL" and "Published at" qualifiers.  Either of
        # them could contain a Flickr URL.
        url = get_single_qualifier(page_id, statement, property_id=WikidataProperties.Url)
        published_at = get_single_qualifier(
            page_id, statement, property_id=WikidataProperties.DescribedAtUrl
        )

        for u in (url, published_at):
            if u is None:
                continue

            if u["datavalue"]["type"] != "string":
                assert 0
                continue

            try:
                parsed_url = parse_flickr_url(u["datavalue"]["value"])
            except (UnrecognisedUrl, NotAFlickrUrl):
                pass
            else:
                if parsed_url["type"] == "single_photo":
                    candidates.add(parsed_url["photo_id"])
                else:
                    raise AmbiguousStructuredData(f"Ambiguous URL in {page_id}: {u['datavalue']['value']}")

    # Look for a photo ID in the "Flickr Photo ID" field.
    for statement in sdc.get(WikidataProperties.FlickrPhotoId, []):
        if statement["mainsnak"]["datavalue"]["type"] == "string":
            candidates.add(statement["mainsnak"]["datavalue"]["value"])
        else:
            assert 0

    if len(candidates) == 1:
        return candidates.pop()
    elif len(candidates) > 1:
        raise ValueError(f"Ambiguous set of Flickr photo IDs: {candidates}")
    else:
        return None
