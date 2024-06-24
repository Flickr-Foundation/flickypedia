import datetime
import functools
import re
import typing

from flask import current_app
import httpx

from flickypedia.types.structured_data import DataValueTypes, Value


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
        "cc0-1.0": "Q6938433",
        "usgov": "Q60671452",
        "pdm": "Q19652",
    }


class WikidataDatePrecision:
    """
    Named constants for precision in the Wikidata model.

    See https://www.wikidata.org/wiki/Help:Dates#Precision
    """

    Year = 9
    Month = 10
    Day = 11


@functools.lru_cache
def get_entity_label(entity_id: str) -> str | None:
    """
    Look up the name of a Wikidata entity.

    TODO: Currently this only returns the English label, but the API
    returns labels in multiple languages.  This might be a good point
    to do some internationalisation.
    """
    resp = httpx.get(
        f"https://www.wikidata.org/w/rest.php/wikibase/v0/entities/items/{entity_id}",
        headers={"User-Agent": current_app.config["USER_AGENT"]},
    )

    try:
        resp.raise_for_status()
        return resp.json()["labels"]["en"]  # type: ignore
    except Exception:  # pragma: no cover
        return None


def to_wikidata_date_value(
    d: datetime.datetime, *, precision: typing.Literal["day", "month", "year"]
) -> DataValueTypes.Time:
    """
    Convert a Python native-datetime to the Wikidata data model.

    See https://www.wikidata.org/wiki/Help:Dates#Precision
    """
    assert precision in ("day", "month", "year")

    # This is the timestamp, e.g. ``+2023-10-11T00:00:00Z``.
    #
    # We zero the hour/minute/second even if we have that precision
    # in our datetime because of a limitation in Wikidata.
    # In particular, as of 12 October 2023:
    #
    #     "time" field can not be saved with precision higher
    #     than a "day".
    #
    # If Wikidata ever relaxes this restriction, we could revisit
    # this decision.
    #
    # Note: the decision to zero the unused fields is to match the
    # behaviour of the SDC visual editor in the browser -- if you
    # set a value with e.g. month precision, the day is set to "00".
    time_str = {
        "day": d.strftime("+%Y-%m-%dT00:00:00Z"),
        "month": d.strftime("+%Y-%m-00T00:00:00Z"),
        "year": d.strftime("+%Y-00-00T00:00:00Z"),
    }[precision]

    precision_value = {
        "day": WikidataDatePrecision.Day,
        "month": WikidataDatePrecision.Month,
        "year": WikidataDatePrecision.Year,
    }[precision]

    # This is the numeric offset from UTC in minutes.  All the timestamps
    # we get from Flickr are in UTC, so we can default this to 0.
    timezone = 0

    # These are qualifiers for how many units before/after the given time
    # we could be, except they're not actually used by Wikidata.
    # As of 12 October 2023:
    #
    #     We do not use before and after fields and use qualifiers
    #     instead to indicate time period.
    #
    # But the API returns an error if you try to post a date without these,
    # so we include default values.
    before = after = 0

    # This tells Wikidata which calendar we're using.
    #
    # Although this is the default, the API throws an error if you try
    # to store a date without it, so we include it here.
    calendarmodel = (
        f"http://www.wikidata.org/entity/{WikidataEntities.GregorianCalendar}"
    )

    return {
        "value": {
            "time": time_str,
            "precision": precision_value,
            "timezone": timezone,
            "before": before,
            "after": after,
            "calendarmodel": calendarmodel,
        },
        "type": "time",
    }


def to_wikidata_entity_value(*, entity_id: str) -> DataValueTypes.WikibaseEntityId:
    """
    Create a datavalue for a Wikidata entity.
    """
    assert re.match(r"^Q[0-9]+$", entity_id)

    return {
        "value": {
            "id": entity_id,
            "entity-type": "item",
            "numeric-id": int(entity_id.replace("Q", "")),
        },
        "type": "wikibase-entityid",
    }


def to_wikidata_string_value(*, value: str) -> DataValueTypes.String:
    """
    Create a datavalue for a literal string.
    """
    return {"value": value, "type": "string"}


def render_wikidata_date(value: Value.Time) -> str:
    """
    Given a Wikidata date from the SDC, render it as text.
    """
    assert (
        value["calendarmodel"]
        == f"http://www.wikidata.org/entity/{WikidataEntities.GregorianCalendar}"
    )
    assert value["precision"] in {11, 10, 9}

    # This is the numeric value of precision used in the Wikidata model.
    #
    # See https://www.wikidata.org/wiki/Help:Dates#Precision
    if value["precision"] == 11:
        d = datetime.datetime.strptime(value["time"], "+%Y-%m-%dT00:00:00Z")
        return d.strftime("%-d %B %Y")
    elif value["precision"] == 10:
        d = datetime.datetime.strptime(value["time"], "+%Y-%m-00T00:00:00Z")
        return d.strftime("%B %Y")
    elif value["precision"] == 9:
        d = datetime.datetime.strptime(value["time"], "+%Y-00-00T00:00:00Z")
        return d.strftime("%Y")
    else:  # pragma: no cover
        assert False
