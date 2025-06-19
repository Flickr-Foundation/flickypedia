import functools

import httpx


class WikidataEntities:
    """
    Named constants for certain Wikidata entities.
    """

    # To see documentation for a particular property, go to
    # https://www.wikidata.org/wiki/<ENTITY_ID>
    #
    # e.g. https://www.wikidata.org/wiki/Q103204
    Circa = "Q5727902"
    Copyrighted = "Q50423863"
    DedicatedToPublicDomainByCopyrightOwner = "Q88088423"
    FileAvailableOnInternet = "Q74228490"
    Flickr = "Q103204"
    GregorianCalendar = "Q1985727"
    NationalLibraryOfFinland = "Q420747"
    PublicDomain = "Q19652"
    StatedByCopyrightHolderAtSourceWebsite = "Q61045577"
    UnitedStatesOfAmerica = "Q30"
    WorkOfTheFederalGovernmentOfTheUnitedStates = "Q60671452"

    # We only map the license types used by Flickypedia -- we should
    # never be creating SDC for e.g. CC BY-NC.
    Licenses = {
        "cc-by-2.0": "Q19125117",
        "cc-by-sa-2.0": "Q19068220",
        "cc-by-4.0": "Q20007257",
        "cc-by-sa-4.0": "Q18199165",
        "cc0-1.0": "Q6938433",
        "usgov": "Q60671452",
        "pdm": "Q19652",
    }


@functools.lru_cache
def get_wikidata_entity_label(entity_id: str) -> str | None:
    """
    Look up the label of a Wikidata entity.

    TODO: Currently this only returns the English label, but the API
    returns labels in multiple languages.  This might be a good point
    to do some internationalisation.
    """
    resp = httpx.get(
        f"https://www.wikidata.org/w/rest.php/wikibase/v0/entities/items/{entity_id}"
    )

    try:
        resp.raise_for_status()
        return resp.json()["labels"]["en"]  # type: ignore
    except Exception:  # pragma: no cover
        return None
