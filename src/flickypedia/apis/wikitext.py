"""
Create Wikitext for display on Wikimedia Commons.

== Useful reading ==

*   Help:Wikitext
    https://en.wikipedia.org/wiki/Help:Wikitext

"""

from flickypedia.apis.flickr import TakenDateGranularity
from flickypedia.types import DateTaken, FlickrUser


def create_wikitext(
    photo_url: str, date_taken: DateTaken, flickr_user: FlickrUser, license_id: str
) -> str:
    """
    Creates the Wikitext for a Flickr photo being uploaded to Wiki Commons.
    """
    # The date is formatted with varying degrees of granularity.
    #
    # For dates which are circa or unknown from the Flickr API, we use
    # two Wikimedia templates for rendering this sort of data.
    #
    # See https://commons.wikimedia.org/wiki/Template:Circa
    # See https://commons.wikimedia.org/wiki/Template:Unknown
    #
    date_format_string = {
        TakenDateGranularity.Second: "%Y-%m-%d %H:%M:%S",
        TakenDateGranularity.Month: "%Y-%m",
        TakenDateGranularity.Year: "%Y",
        TakenDateGranularity.Circa: "{{circa|%Y}}",
    }[date_taken["granularity"]]

    if date_taken["unknown"]:
        date_string = "{{Other date|?}}"
    else:
        date_string = date_taken["value"].strftime(date_format_string)

    return """=={{int:filedesc}}==
{{Information
|Source=[%s]
|Date=%s
|Author=[https://www.flickr.com/people/%s %s]
|Permission=
|other_versions=
}}

=={{int:license-header}}==
{{%s}}
""" % (
        photo_url,
        date_string,
        flickr_user["id"],
        flickr_user["realname"] or flickr_user["username"],
        license_id,
    )
