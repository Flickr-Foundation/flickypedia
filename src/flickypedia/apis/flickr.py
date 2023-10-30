"""
This file contains some methods for calling the Flickr API.
"""

import datetime
import functools
from typing import Optional, TypedDict
import xml.etree.ElementTree as ET

import httpx


class TakenDateGranularity:
    """
    Named constants for Flickr "Taken date" granularity.

    See https://www.flickr.com/services/api/misc.dates.html
    """

    Second = 0
    Month = 4
    Year = 6
    Circa = 8


class SafetyLevel:
    """
    Named constants for Flickr Safety Levels.

    See https://www.flickrhelp.com/hc/en-us/articles/4404064206996-Content-filters
    """

    Safe = 0
    Moderate = 1
    Restricted = 2


class DateTaken(TypedDict):
    value: datetime.datetime
    granularity: int
    unknown: bool


class FlickrUser(TypedDict):
    id: str
    username: str
    realname: Optional[str]
    photos_url: str
    profile_url: str


class FlickrApi:
    """
    This is a thin wrapper for calling the Flickr API.

    It doesn't do much interesting stuff; the goal is just to reduce boilerplate
    in the rest of the codebase, e.g. have the XML parsing in one place rather
    than repeated everywhere.
    """

    def __init__(self, *, api_key, user_agent):
        self.client = httpx.Client(
            base_url="https://api.flickr.com/services/rest/",
            params={"api_key": api_key},
            headers={"User-Agent": user_agent},
        )

    def call(self, method, **params):
        params["method"] = method

        resp = self.client.get(url="", params=params)
        resp.raise_for_status()

        # Note: the xml.etree.ElementTree is not secure against maliciously
        # constructed data (see warning in the Python docs [1]), but that's
        # fine here -- we're only using it for responses from the Flickr API,
        # which we trust.
        #
        # [1]: https://docs.python.org/3/library/xml.etree.elementtree.html
        xml = ET.fromstring(resp.text)

        # If the Flickr API call fails, it will return a block of XML like:
        #
        #       <rsp stat="fail">
        #       	<err
        #               code="1"
        #               msg="Photo &quot;1211111111111111&quot; not found (invalid ID)"
        #           />
        #       </rsp>
        #
        # Different API endpoints have different codes, and so we just throw
        # and let calling functions decide how to handle it.
        if xml.attrib["stat"] == "fail":
            errors = xml.find(".//err").attrib

            # Although I haven't found any explicit documentation of this,
            # it seems like a pretty common convention that error code "1"
            # means "not found".
            if errors["code"] == "1":
                raise ResourceNotFound(**params)
            else:
                raise FlickrApiException(errors)

        return xml

    @functools.lru_cache
    def get_licenses(self):
        """
        Returns a list of licenses, arranged by code.
        """
        license_resp = self.call("flickr.photos.licenses.getInfo")

        result = {}

        # Add a short ID which can be used to more easily refer to this
        # license throughout the codebase.
        license_ids = {
            "All Rights Reserved": "in-copyright",
            "Attribution-NonCommercial-ShareAlike License": "cc-by-nc-sa-2.0",
            "Attribution-NonCommercial License": "cc-by-nc-2.0",
            "Attribution-NonCommercial-NoDerivs License": "cc-by-nc-nd-2.0",
            "Attribution License": "cc-by-2.0",
            "Attribution-ShareAlike License": "cc-by-sa-2.0",
            "Attribution-NoDerivs License": "cc-by-nd-2.0",
            "No known copyright restrictions": "nkcr",
            "United States Government Work": "usgov",
            "Public Domain Dedication (CC0)": "cc0-1.0",
            "Public Domain Mark": "pdm",
        }

        license_labels = {
            "Attribution-NonCommercial-ShareAlike License": "CC BY-NC-SA 2.0",
            "Attribution-NonCommercial License": "CC BY-NC 2.0",
            "Attribution-NonCommercial-NoDerivs License": "CC BY-NC-ND 2.0",
            "Attribution License": "CC BY 2.0",
            "Attribution-ShareAlike License": "CC BY-SA 2.0",
            "Attribution-NoDerivs License": "CC BY-ND 2.0",
            "Public Domain Dedication (CC0)": "CC0 1.0",
        }

        for lic in license_resp.findall(".//license"):
            result[lic.attrib["id"]] = {
                "id": license_ids[lic.attrib["name"]],
                "label": license_labels.get(lic.attrib["name"], lic.attrib["name"]),
                "url": lic.attrib["url"] or None,
            }

        return result

    @functools.lru_cache(maxsize=None)
    def lookup_license_code(self, *, license_code: str):
        """
        Given a license code from the Flickr API, return the license data.

        e.g. a Flickr API response might include a photo in the following form:

            <photo license="0" …>

        Then you'd call this function to find out what that means:

            >>> lookup_license_code(api, license_code="0")
            {"id": "in-copyright", "name": "All Rights Reserved", "url": ""}

        """
        licenses = self.get_licenses()
        return licenses[license_code]

    def lookup_user(self, *, user_url: str):
        """
        Given the link to a user's photos or profile, return their info.

            >>> lookup_user_id_from_url("https://www.flickr.com/photos/britishlibrary/")
            {
                "id": "12403504@N02",
                "username": "The British Library",
                "realname": "British Library",
                "photos_url": "https://www.flickr.com/photos/britishlibrary/",
                "profile_url": "https://www.flickr.com/people/britishlibrary/",
            }

        """
        # The lookupUser response is of the form:
        #
        #       <user id="12403504@N02">
        #       	<username>The British Library</username>
        #       </user>
        #
        resp = self.call("flickr.urls.lookupUser", url=user_url)
        user_id = resp.find(".//user").attrib["id"]

        # The getInfo response is of the form:

        #     <person id="12403504@N02"…">
        #   	<username>The British Library</username>
        #       <realname>British Library</realname>
        #       <photosurl>https://www.flickr.com/photos/britishlibrary/</photosurl>
        #       <profileurl>https://www.flickr.com/people/britishlibrary/</profileurl>
        #       …
        #     </person>
        #
        resp = self.call("flickr.people.getInfo", user_id=user_id)
        username = resp.find(".//username").text
        photos_url = resp.find(".//photosurl").text
        profile_url = resp.find(".//profileurl").text

        try:
            realname = resp.find(".//realname").text
        except AttributeError:
            realname = None

        return {
            "id": user_id,
            "username": username,
            "realname": realname,
            "photos_url": photos_url,
            "profile_url": profile_url,
        }

    def get_single_photo(self, *, photo_id: str):
        """
        Look up the information for a single photo.
        """
        info_resp = self.call("flickr.photos.getInfo", photo_id=photo_id)
        sizes_resp = self.call("flickr.photos.getSizes", photo_id=photo_id)

        # The getInfo response is a blob of XML of the form:
        #
        #       <?xml version="1.0" encoding="utf-8" ?>
        #       <rsp stat="ok">
        #       <photo license="8" …>
        #       	<owner
        #               nsid="30884892@N08
        #               username="U.S. Coast Guard"
        #               realname="Coast Guard" …
        #           >
        #       		…
        #       	</owner>
        #       	<title>Puppy Kisses</title>
        #           <description>Seaman Nina Bowen shows …</description>
        #       	<dates
        #               posted="1490376472"
        #               taken="2017-02-17 00:00:00"
        #               …
        #           />
        #       	<urls>
        #       		<url type="photopage">https://www.flickr.com/photos/coast_guard/32812033543/</url>
        #       	</urls>
        #           …
        #       </photo>
        #       </rsp>
        #
        title = info_resp.find(".//photo/title").text
        description = info_resp.find(".//photo/description").text or None

        user_id = info_resp.find(".//photo/owner").attrib["nsid"]
        path_alias = info_resp.find(".//photo/owner").attrib["path_alias"] or user_id

        owner = {
            "id": user_id,
            "username": info_resp.find(".//photo/owner").attrib["username"],
            "realname": info_resp.find(".//photo/owner").attrib["realname"] or None,
            "photos_url": f"https://www.flickr.com/photos/{path_alias}/",
            "profile_url": f"https://www.flickr.com/people/{path_alias}/",
        }

        dates = info_resp.find(".//photo/dates").attrib

        date_posted = _parse_date_posted(dates["posted"])

        date_taken = {
            "value": _parse_date_taken(dates["taken"]),
            "granularity": int(dates["takengranularity"]),
            "unknown": dates["takenunknown"] == "1",
        }

        photo_page_url = info_resp.find('.//photo/urls/url[@type="photopage"]').text

        license = self.lookup_license_code(
            license_code=info_resp.find(".//photo").attrib["license"]
        )

        safety_level = int(info_resp.find(".//photo").attrib["safety_level"])

        # The getSizes response is a blob of XML of the form:
        #
        #       <?xml version="1.0" encoding="utf-8" ?>
        #       <rsp stat="ok">
        #       <sizes canblog="0" canprint="0" candownload="1">
        #           <size
        #               label="Square"
        #               width="75"
        #               height="75"
        #               source="https://live.staticflickr.com/2903/32812033543_c1b3784192_s.jpg"
        #               url="https://www.flickr.com/photos/coast_guard/32812033543/sizes/sq/"
        #               media="photo"
        #           />
        #           <size
        #               label="Large Square"
        #               width="150"
        #               height="150"
        #               source="https://live.staticflickr.com/2903/32812033543_c1b3784192_q.jpg"
        #               url="https://www.flickr.com/photos/coast_guard/32812033543/sizes/q/"
        #               media="photo"
        #           />
        #           …
        #       </sizes>
        #       </rsp>
        #
        # Within this function, we just return all the sizes -- we leave it up to the
        # caller to decide which size is most appropriate for their purposes.
        sizes = [s.attrib for s in sizes_resp.findall(".//size")]

        for s in sizes:
            s["width"] = int(s["width"])
            s["height"] = int(s["height"])

        return {
            "id": photo_id,
            "title": title,
            "description": description,
            "owner": owner,
            "date_posted": date_posted,
            "date_taken": date_taken,
            "safety_level": safety_level,
            "license": license,
            "url": photo_page_url,
            "sizes": sizes,
        }

    # There are a bunch of similar flickr.XXX.getPhotos methods;
    # these are some constants and utility methods to help when
    # calling them.
    extras = [
        "license",
        "date_upload",
        "date_taken",
        "media",
        "owner_name",
        "url_sq",
        "url_t",
        "url_s",
        "url_m",
        "url_o",
        # These parameters aren't documented, but they're quite
        # useful for our purposes!
        "url_q",  # Large Square
        "url_l",  # Large
        "description",
        "safety_level",
    ]

    def _parse_collection_of_photos_response(self, elem):
        # The wrapper element includes a couple of attributes related
        # to pagination, e.g.
        #
        #     <photoset pages="1" total="2" …>
        #
        page_count = int(elem.attrib["pages"])
        total_photos = int(elem.attrib["total"])

        photos = []

        for photo_elem in elem.findall(".//photo"):
            title = photo_elem.attrib["title"] or None
            description = photo_elem.find(".//description").text or None

            photos.append(
                {
                    "_elem": photo_elem,
                    "id": photo_elem.attrib["id"],
                    "title": title,
                    "description": description,
                    "date_posted": _parse_date_posted(photo_elem.attrib["dateupload"]),
                    "date_taken": {
                        "value": _parse_date_taken(photo_elem.attrib["datetaken"]),
                        "granularity": int(photo_elem.attrib["datetakengranularity"]),
                        "unknown": photo_elem.attrib["datetakenunknown"] == "1",
                    },
                    "license": self.lookup_license_code(
                        license_code=photo_elem.attrib["license"]
                    ),
                    "sizes": _parse_sizes(photo_elem),
                    "safety_level": int(photo_elem.attrib["safety_level"]),
                }
            )

        return {
            "page_count": page_count,
            "total_photos": total_photos,
            "photos": photos,
        }

    def get_photos_in_album(self, *, user_url, album_id, page=1, per_page=10):
        """
        Get the photos in an album.
        """
        user = self.lookup_user(user_url=user_url)

        # https://www.flickr.com/services/api/flickr.photosets.getPhotos.html
        resp = self.call(
            "flickr.photosets.getPhotos",
            user_id=user["id"],
            photoset_id=album_id,
            extras=",".join(self.extras),
            page=page,
            per_page=per_page,
        )

        parsed_resp = self._parse_collection_of_photos_response(
            resp.find(".//photoset")
        )

        for p in parsed_resp["photos"]:
            p["owner"] = user
            p["url"] = user["photos_url"] + p.pop("_elem").attrib["id"] + "/"

        # https://www.flickr.com/services/api/flickr.photosets.getInfo.html
        album_resp = self.call(
            "flickr.photosets.getInfo", user_id=user["id"], photoset_id=album_id
        )
        album_title = album_resp.find(".//title").text

        return {
            "photos": parsed_resp["photos"],
            "page_count": parsed_resp["page_count"],
            "total_photos": parsed_resp["total_photos"],
            "album": {"owner": user, "title": album_title},
        }


class FlickrApiException(Exception):
    """
    Base class for all exceptions thrown from the Flickr API.
    """

    pass


class ResourceNotFound(FlickrApiException):
    """
    Thrown when you try to look up a resource that doesn't exist.
    """

    def __init__(self, method, **params):
        super().__init__(
            f"Unable to find resource at {method} with properties {params}"
        )


def _parse_date_posted(p):
    # See https://www.flickr.com/services/api/misc.dates.html
    #
    #     The posted date is always passed around as a unix timestamp,
    #     which is an unsigned integer specifying the number of seconds
    #     since Jan 1st 1970 GMT.
    #
    # e.g. '1490376472'
    return datetime.datetime.fromtimestamp(int(p), tz=datetime.timezone.utc)


def _parse_date_taken(p):
    # See https://www.flickr.com/services/api/misc.dates.html
    #
    #     The date taken should always be displayed in the timezone
    #     of the photo owner, which is to say, don't perform
    #     any conversion on it.
    #
    # e.g. '2017-02-17 00:00:00'
    return datetime.datetime.strptime(p, "%Y-%m-%d %H:%M:%S")


def _parse_sizes(photo_elem):
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
    sizes = []

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
