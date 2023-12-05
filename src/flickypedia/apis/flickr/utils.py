import datetime
import xml.etree.ElementTree as ET

from flickypedia.types.flickr import SafetyLevel, Size, TakenGranularity


def parse_date_posted(p: str) -> datetime.datetime:
    # See https://www.flickr.com/services/api/misc.dates.html
    #
    #     The posted date is always passed around as a unix timestamp,
    #     which is an unsigned integer specifying the number of seconds
    #     since Jan 1st 1970 GMT.
    #
    # e.g. '1490376472'
    return datetime.datetime.fromtimestamp(int(p), tz=datetime.timezone.utc)


def parse_date_taken(p: str) -> datetime.datetime:
    # See https://www.flickr.com/services/api/misc.dates.html
    #
    #     The date taken should always be displayed in the timezone
    #     of the photo owner, which is to say, don't perform
    #     any conversion on it.
    #
    # e.g. '2017-02-17 00:00:00'
    return datetime.datetime.strptime(p, "%Y-%m-%d %H:%M:%S")


def parse_date_taken_granularity(g: str) -> TakenGranularity:
    """
    Converts a numeric granularity level in the Flickr API into a
    human-readable value.

    See https://www.flickr.com/services/api/misc.dates.html
    """
    lookup_table: dict[str, TakenGranularity] = {
        "0": "second",
        "4": "month",
        "6": "year",
        "8": "circa",
    }

    try:
        return lookup_table[g]
    except KeyError:
        raise ValueError(f"Unrecognised date granularity: {g}")


def parse_safety_level(s: str) -> SafetyLevel:
    """
    Converts a numeric safety level ID in the Flickr API into
    a human-readable value.

    See https://www.flickrhelp.com/hc/en-us/articles/4404064206996-Content-filters
    """
    lookup_table: dict[str, SafetyLevel] = {
        "0": "safe",
        "1": "moderate",
        "2": "restricted",
    }

    try:
        return lookup_table[s]
    except KeyError:
        raise ValueError(f"Unrecognised safety level: {s}")


def parse_sizes(photo_elem: ET.Element) -> list[Size]:
    """
    Get a list of sizes from a photo in a collection response.
    """
    # When you get a collection of photos (e.g. in an album)
    # you can get some of the sizes on the <photo> element, e.g.
    #
    #     <
    #       photo
    #       url_t="https://live.staticflickr.com/2893/1234567890_t.jpg"
    #       height_t="78"
    #       width_t="100"
    #       …
    #     />
    #
    sizes: list[Size] = []

    for suffix, label in [
        ("sq", "Square"),
        ("q", "Large Square"),
        ("t", "Thumbnail"),
        ("s", "Small"),
        ("m", "Medium"),
        ("l", "Large"),
        ("o", "Original"),
    ]:
        try:
            sizes.append(
                {
                    "height": int(photo_elem.attrib[f"height_{suffix}"]),
                    "width": int(photo_elem.attrib[f"width_{suffix}"]),
                    "label": label,
                    "media": photo_elem.attrib["media"],
                    "source": photo_elem.attrib[f"url_{suffix}"],
                }
            )
        except KeyError:
            pass

    return sizes
