from flickr_photos_api import LocationInfo

from ..types import NewStatement
from ..wikidata_properties import WikidataProperties


def create_location_statement(location: LocationInfo | None) -> NewStatement | None:
    """
    Creates a structured data statement for the "coordinates of
    the point of view" statement.

    This is the location of the camera, not the location of the subject.
    There were several discussions about this in the Flickr.org Slack and
    this was agreed as the most suitable.

    See https://flickrfoundation.slack.com/archives/C05AVC1JYL9/p1696947242703349
    """
    if location is None:
        return None

    # Some Flickr photos have "null coordinates" -- location data which
    # is obviously nonsensical.
    #
    # e.g. https://www.flickr.com/photos/ed_webster/16125227798/
    #
    #     <location latitude="0.000000" longitude="0.000000" accuracy="16" context="0">
    #       <neighbourhood woeid="0"/>
    #     </location>
    #
    # In this case we should just discard the information as useless, rather
    # than write null coordinates into WMC.
    #
    # See https://github.com/Flickr-Foundation/flickypedia/issues/461
    if location == {"accuracy": 16, "latitude": 0.0, "longitude": 0.0}:
        return None

    # The accuracy parameter in the Flickr API response tells us
    # the precision of the location information (15 November 2023):
    #
    #     Recorded accuracy level of the location information.
    #     World level is 1, Country is ~3, Region ~6, City ~11, Street ~16.
    #     Current range is 1-16.
    #
    # Flickr doesn't publish any definitive stats on how their accuracy
    # levels map to absolute position on the Earth, so I had to make
    # some rough guesses.  This information is already approximate, so
    # I figure this is probably okay.
    #
    # ============
    # How I did it
    # ============
    #
    # If you look at the map view on Flickr (https://www.flickr.com/map/),
    # there are 17 different zoom levels, which correspond to the
    # different accuracies (0-17, although you can't see accuracy 0
    # on new photos).
    #
    # For each zoom/accuracy level:
    #
    #   1.  Create a new property for "coordinates of the point of view"
    #       in the Wikimedia Commons SDC visual editor.
    #   2.  Click "Select on map"
    #   3.  Zoom the map to roughly match the Flickr map (using the
    #       scale as a guide)
    #   4.  Click a point on the map
    #
    # At this point Wikimedia zooms to a fixed level, and updates its own
    # value for precision (to 1/1000 of an arcsecond, ±0.0001°, etc.)
    #
    # Use that value for precision.
    try:
        wikidata_precision = {
            # Flickr = 50m / WMC = ±0.000001°
            16: 1e-05,
            # Flickr = 100m, 300m / WMC = 1/10 of an arcsecond
            15: 2.777777777777778e-05,
            14: 2.777777777777778e-05,
            # Flickr = 500m, 1km / WMC = ±0.0001°
            13: 0.0001,
            12: 0.0001,
            # Flickr = 3km / WMC = to an arcsecond
            11: 0.0002777777777777778,
            # Flickr = 5km, 10km, 20km, 50km  / WMC = ±0.001°
            10: 0.001,
            9: 0.001,
            8: 0.001,
            7: 0.001,
            # Flickr =  100km / WMC = ±0.01°
            6: 0.01,
            # Flickr =  200km, 300km / WMC = to an arcminute
            5: 0.016666666666666666,
            4: 0.016666666666666666,
            # Flickr = 500km, 1000km, 3000km / WMC = ±0.1°
            3: 0.1,
            2: 0.1,
            1: 0.1,
        }[location["accuracy"]]
    except KeyError:
        raise ValueError(f'Unrecognised location accuracy: {location["accuracy"]}')

    return {
        "mainsnak": {
            "datavalue": {
                "type": "globecoordinate",
                "value": {
                    "altitude": None,
                    "globe": "http://www.wikidata.org/entity/Q2",
                    "latitude": location["latitude"],
                    "longitude": location["longitude"],
                    "precision": wikidata_precision,
                },
            },
            "property": WikidataProperties.CoordinatesOfThePointOfView,
            "snaktype": "value",
        },
        "type": "statement",
    }
