import datetime
import functools
import re
from typing import Optional

from flask import current_app
import httpx

from ._types import DateValue, WikidataTime


class WikidataProperties:
    """
    Named constants for Wikidata property names.
    """

    # To see documentation for a particular property, go to
    # https://www.wikidata.org/wiki/Property:<PROPERTY_ID>
    #
    # e.g. https://www.wikidata.org/wiki/Property:P2093
    Operator = "P137"
    Creator = "P170"
    DescribedAtUrl = "P973"
    AuthorName = "P2093"
    FlickrUserId = "P3267"
    Url = "P2699"
    SourceOfFile = "P7482"
    CopyrightLicense = "P275"
    CopyrightStatus = "P6216"
    Inception = "P571"
    PublicationDate = "P577"
    PublishedIn = "P1433"
    SourcingCircumstances = "P1480"


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
    FileAvailableOnInternet = "Q74228490"
    Flickr = "Q103204"
    GregorianCalendar = "Q1985727"

    # We only map the license types used by Flickypedia -- we should
    # never be creating SDC for e.g. CC BY-NC.
    Licenses = {
        "cc-by-2.0": "Q19125117",
        "cc-by-sa-2.0": "Q19068220",
        "cc0-1.0": "Q6938433",
        "usgov": "Q60671452",
        "pdm": "Q19652",
    }


@functools.lru_cache
def get_property_name(code: str) -> str:
    """
    Look up the name of a Wikidata property.

        >>> get_property_name(code="P137")
        "operator"

        >>> get_property_name(code="P2093")
        "author name"

    """
    for attr in dir(WikidataProperties):
        if getattr(WikidataProperties, attr) == code:
            return " ".join(re.findall("[A-Z][^A-Z]*", attr)).lower()

    # We never expect to end up here -- we're not using this to show
    # the labels of arbitrary SDC, just the ones we're going to add.
    else:  # pragma: no cover
        raise KeyError


@functools.lru_cache
def get_entity_label(entity_id: str) -> Optional[str]:
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


@functools.lru_cache
def lookup_flickr_user_in_wikidata(user_id: str, username: str) -> Optional[str]:
    """
    Return the Wikidata entity for a Flickr user, if it exists.

        >>> lookup_flickr_user_in_wikidata(user_id="1234567@N02", username="brandnew")
        None

        >>> lookup_flickr_user_in_wikidata(user_id="199246608@N02", username="ianemes")
        "Q5981474"

    Note that Wikidata entities are inconsistent about using the user ID
    (the numeric form) or the screen name  (which you see in URL slugs).
    For completeness of coverage, we search by both, if available.

    """
    # These two queries are looking for Wikidata entities which have
    # property P3267 (Flickr user ID) with the given value (id and name).
    #
    # I used https://stackoverflow.com/a/27212955/1558022 as the
    # starting point for these SPARQL queries.
    if username is None:
        query = """PREFIX wdt: <http://www.wikidata.org/prop/direct/>

        SELECT ?item WHERE {
          { ?item wdt:%s "%s" . }
        }""" % (
            WikidataProperties.FlickrUserId,
            user_id,
        )
    else:
        query = """PREFIX wdt: <http://www.wikidata.org/prop/direct/>

        SELECT ?item WHERE {
          { ?item wdt:%s "%s" . }
          UNION
          { ?item wdt:%s "%s" . }
        }""" % (
            WikidataProperties.FlickrUserId,
            user_id,
            WikidataProperties.FlickrUserId,
            username,
        )

    resp = httpx.get(
        "https://query.wikidata.org/sparql",
        params={"format": "json", "query": query},
        headers={"User-Agent": current_app.config["USER_AGENT"]},
    )

    resp.raise_for_status()

    # The returned result from the SPARQL query looks something like this:
    #
    #     {
    #       "head": {"vars": ["item", "itemLabel"]},
    #       "results": {
    #         "bindings": [
    #           {
    #             "item": {
    #               "type": "uri",
    #               "value": "http://www.wikidata.org/entity/Q5981474"
    #             }
    #           }
    #         ]
    #       }
    #     }
    #
    results = resp.json()["results"]["bindings"]

    # The list of matched entities is returned as a list.  In theory
    # we could get two or more entities back, in which case it's unclear
    # where we should map it -- in this case, log a warning and then give up.
    if len(results) > 1:
        print(
            "Warning: ambiguous Wikidata entities found for "
            f"Flickr user id={user_id} / username={username}"
        )
        return None

    # Look for something that looks like a single Wikidata entity URL
    # in the response.
    #
    # We're deliberately quite conservative here -- it's better to skip
    # linking an entity that exists that link an incorrect entity.
    try:
        matched_item = results[0]["item"]

        # e.g. http://www.wikidata.org/entity/Q5981474
        uri_match = re.match(
            r"^http://www\.wikidata\.org/entity/(?P<wikidata_id>Q\d+)$",
            matched_item["value"],
        )

        if matched_item["type"] == "uri" and uri_match is not None:
            return uri_match.group("wikidata_id")

        # This branch is defensive -- I've yet to see a query where
        # we got a non-Wikidata URI here, and I'm not sure that makes
        # any sense, but we include a meaningful error message just in case.
        else:  # pragma: no cover
            raise RuntimeError(
                f"Unexpected result from the Wikidata API: {matched_item}"
            )

    except (IndexError, KeyError):
        return None


def to_wikidata_date(d: datetime.datetime, *, precision: str) -> WikidataTime:
    """
    Convert a Python native-datetime to the Wikidata data model.

    See https://www.wikidata.org/wiki/Help:Dates#Precision
    """
    if precision not in ("day", "month", "year"):
        raise ValueError("Unrecognised precision: {precision}")

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
    time_str = {
        "day": d.strftime("+%Y-%m-%dT00:00:00Z"),
        "month": d.strftime("+%Y-%m-00T00:00:00Z"),
        "year": d.strftime("+%Y-00-00T00:00:00Z"),
    }[precision]

    # This is the numeric value of precision used in the Wikidata model.
    #
    # See https://www.wikidata.org/wiki/Help:Dates#Precision
    precision_value = {"day": 11, "month": 10, "year": 9}[precision]

    # This is the numeric offset from UTC in minutes.  All the timestamps
    # we get from Flickr are in UTC, so we can default this to 0.
    timezone = 0

    # These are qualifiers for how many units before/after the given time
    # we could be, execpt they're not actually used by Wikidata.
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


def render_wikidata_date(value: DateValue) -> str:
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
        return "%s (precision: day, calendar: Gregorian)" % d.strftime("%-d %B %Y")
    elif value["precision"] == 10:
        d = datetime.datetime.strptime(value["time"], "+%Y-%m-00T00:00:00Z")
        return "%s (precision: month, calendar: Gregorian)" % d.strftime("%B %Y")
    elif value["precision"] == 9:
        d = datetime.datetime.strptime(value["time"], "+%Y-00-00T00:00:00Z")
        return "%s (precision: year, calendar: Gregorian)" % d.strftime("%Y")
    else:  # pragma: no cover
        assert False
