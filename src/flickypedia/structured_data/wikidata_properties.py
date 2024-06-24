import re


class WikidataProperties:
    """
    Named constants for Wikidata properties.
    """

    # To see documentation for a particular property, go to
    # https://www.wikidata.org/wiki/Property:<PROPERTY_ID>
    #
    # e.g. https://www.wikidata.org/wiki/Property:P2093
    Operator = "P137"
    AppliesToJurisdiction = "P1001"
    Creator = "P170"
    DescribedAtUrl = "P973"
    DeterminationMethod = "P459"
    AuthorName = "P2093"
    CoordinatesOfThePointOfView = "P1259"
    FlickrPhotoId = "P12120"
    FlickrUserId = "P3267"
    Url = "P2699"
    SourceOfFile = "P7482"
    CopyrightLicense = "P275"
    CopyrightStatus = "P6216"
    Inception = "P571"
    PublicationDate = "P577"
    PublishedIn = "P1433"
    Retrieved = "P813"
    SourcingCircumstances = "P1480"


def get_wikidata_property_label(id: str) -> str:
    """
    Look up the label of a Wikidata property.

        >>> get_property_name(id="P137")
        "operator"

        >>> get_property_name(id="P2093")
        "author name"

    """
    if id == "P571":
        return "date created"

    if id == "P1259":
        return "location"

    for attr in dir(WikidataProperties):
        if getattr(WikidataProperties, attr) == id:
            return " ".join(re.findall("[A-Z][^A-Z]*", attr)).lower()

    # We never expect to end up here -- we're not using this to show
    # the labels of arbitrary SDC, just the ones we're going to add.
    else:
        raise KeyError(f"Unrecognised property ID: {id}")
