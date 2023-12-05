import functools
import xml.etree.ElementTree as ET

import httpx

from flickypedia.types.flickr import (
    CollectionOfPhotos,
    DateTaken,
    GroupInfo,
    License,
    LocationInfo,
    PhotosInAlbum,
    PhotosInGallery,
    PhotosInGroup,
    SinglePhoto,
    Size,
    User,
)
from flickypedia.utils import (
    find_optional_text,
    find_required_elem,
    find_required_text,
)
from .exceptions import FlickrApiException, LicenseNotFound, ResourceNotFound
from .utils import (
    parse_date_posted,
    parse_date_taken,
    parse_date_taken_granularity,
    parse_safety_level,
    parse_sizes,
)


class BaseApi:
    """
    This is a thin wrapper for calling the Flickr API.

    It doesn't do much interesting stuff; the goal is just to reduce boilerplate
    in the rest of the codebase, e.g. have the XML parsing in one place rather
    than repeated everywhere.
    """

    def __init__(self, *, api_key: str, user_agent: str) -> None:
        self.client = httpx.Client(
            base_url="https://api.flickr.com/services/rest/",
            params={"api_key": api_key},
            headers={"User-Agent": user_agent},
        )

    def call(self, *, method: str, params: dict[str, str] | None = None) -> ET.Element:
        if params is not None:
            get_params = {"method": method, **params}
        else:
            get_params = {"method": method}

        resp = self.client.get(url="", params=get_params, timeout=15)
        resp.raise_for_status()

        # Note: the xml.etree.ElementTree is not secure against maliciously
        # constructed data (see warning in the Python docs [1]), but that's
        # fine here -- we're only using it for responses from the Flickr API,
        # which we trust.
        #
        # [1]: https://docs.python.org/3/library/xml.etree.elementtree.html
        xml = ET.fromstring(resp.text)

        # print(resp.text)

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
            errors = find_required_elem(xml, path=".//err").attrib

            # Although I haven't found any explicit documentation of this,
            # it seems like a pretty common convention that error code "1"
            # means "not found".
            if errors["code"] == "1":
                raise ResourceNotFound(method, params)
            else:
                raise FlickrApiException(errors)

        return xml


class FlickrPhotosApi(BaseApi):
    @functools.lru_cache()
    def get_licenses(self) -> dict[str, License]:
        """
        Returns a list of licenses, arranged by code.

        See https://www.flickr.com/services/api/flickr.photos.licenses.getInfo.htm
        """
        license_resp = self.call(method="flickr.photos.licenses.getInfo")

        result: dict[str, License] = {}

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
    def lookup_license_by_id(self, *, id: str) -> License:
        """
        Given a license ID from the Flickr API, return the license data.

        e.g. a Flickr API response might include a photo in the following form:

            <photo license="0" …>

        Then you'd call this function to find out what that means:

            >>> api.lookup_license_by_id(id="0")
            {"id": "in-copyright", "name": "All Rights Reserved", "url": None}

        See https://www.flickr.com/services/api/flickr.photos.licenses.getInfo.htm
        """
        licenses = self.get_licenses()

        try:
            return licenses[id]
        except KeyError:
            raise LicenseNotFound(license_id=id)

    def lookup_user_by_url(self, *, url: str) -> User:
        """
        Given the link to a user's photos or profile, return their info.

            >>> api.lookup_user_by_url(user_url="https://www.flickr.com/photos/britishlibrary/")
            {
                "id": "12403504@N02",
                "username": "The British Library",
                "realname": "British Library",
                "photos_url": "https://www.flickr.com/photos/britishlibrary/",
                "profile_url": "https://www.flickr.com/people/britishlibrary/",
                "pathalias": "britishlibrary"
            }

        See https://www.flickr.com/services/api/flickr.urls.lookupUser.htm
        See https://www.flickr.com/services/api/flickr.people.getInfo.htm

        """
        # The lookupUser response is of the form:
        #
        #       <user id="12403504@N02">
        #       	<username>The British Library</username>
        #       </user>
        #
        lookup_resp = self.call(method="flickr.urls.lookupUser", params={"url": url})
        user_id = find_required_elem(lookup_resp, path=".//user").attrib["id"]

        # The getInfo response is of the form:
        #
        #     <person id="12403504@N02" path_alias="britishlibrary" …>
        #   	<username>The British Library</username>
        #       <realname>British Library</realname>
        #       <photosurl>https://www.flickr.com/photos/britishlibrary/</photosurl>
        #       <profileurl>https://www.flickr.com/people/britishlibrary/</profileurl>
        #       …
        #     </person>
        #
        info_resp = self.call(
            method="flickr.people.getInfo", params={"user_id": user_id}
        )

        person_elem = find_required_elem(info_resp, path="person")

        username = find_required_text(person_elem, path="username")
        photos_url = find_required_text(person_elem, path="photosurl")
        profile_url = find_required_text(person_elem, path="profileurl")

        path_alias = person_elem.attrib["path_alias"] or None

        # If the user hasn't set a realname in their profile, the element
        # will be absent from the response.
        realname_elem = person_elem.find(path="realname")

        if realname_elem is None:
            realname = None
        else:
            realname = realname_elem.text

        return {
            "id": user_id,
            "username": username,
            "realname": realname,
            "path_alias": path_alias,
            "photos_url": photos_url,
            "profile_url": profile_url,
        }

    def _get_date_taken(
        self, *, value: str, granularity: str, unknown: bool
    ) -> DateTaken | None:
        # Note: we intentionally omit sending any 'date taken' information
        # to callers if it's unknown.
        #
        # There will be a value in the API response, but if the taken date
        # is unknown, it's defaulted to the date the photo was posted.
        # See https://www.flickr.com/services/api/misc.dates.html
        #
        # This value isn't helpful to callers, so we omit it.  This reduces
        # the risk of somebody skipping the ``unknown`` parameter and using
        # the value in the wrong place.
        if unknown:
            return None
        else:
            return {
                "value": parse_date_taken(value),
                "granularity": parse_date_taken_granularity(granularity),
            }

    def get_single_photo(self, *, photo_id: str) -> SinglePhoto:
        """
        Look up the information for a single photo.
        """
        info_resp = self.call(
            method="flickr.photos.getInfo", params={"photo_id": photo_id}
        )
        sizes_resp = self.call(
            method="flickr.photos.getSizes", params={"photo_id": photo_id}
        )

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
        #           <tags>
        #    		  <tag raw="indian ocean" …>indianocean</tag>
        #           …
        #       </photo>
        #       </rsp>
        #
        photo_elem = find_required_elem(info_resp, path=".//photo")

        title = find_optional_text(photo_elem, path="title")
        description = find_optional_text(photo_elem, path="description")

        owner_elem = find_required_elem(photo_elem, path="owner")
        user_id = owner_elem.attrib["nsid"]
        path_alias = owner_elem.attrib["path_alias"] or None

        owner: User = {
            "id": user_id,
            "username": owner_elem.attrib["username"],
            "realname": owner_elem.attrib["realname"] or None,
            "path_alias": path_alias,
            "photos_url": f"https://www.flickr.com/photos/{path_alias or user_id}/",
            "profile_url": f"https://www.flickr.com/people/{path_alias or user_id}/",
        }

        dates = find_required_elem(photo_elem, path="dates").attrib

        date_posted = parse_date_posted(dates["posted"])

        date_taken = self._get_date_taken(
            value=dates["taken"],
            granularity=dates["takengranularity"],
            unknown=dates["takenunknown"] == "1",
        )

        photo_page_url = find_required_text(
            photo_elem, path='.//urls/url[@type="photopage"]'
        )

        license = self.lookup_license_by_id(id=photo_elem.attrib["license"])

        safety_level = parse_safety_level(photo_elem.attrib["safety_level"])

        # The originalformat parameter will only be returned if the user
        # allows downloads of the photo.
        #
        # We only need this parameter for photos that can be uploaded to
        # Wikimedia Commons.  All CC-licensed photos allow downloads, so
        # we'll always get this parameter for those photos.
        #
        # See https://www.flickr.com/help/forum/32218/
        # See https://www.flickrhelp.com/hc/en-us/articles/4404079715220-Download-permissions
        original_format = photo_elem.get("originalformat")

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
        sizes: list[Size] = []

        for s in sizes_resp.findall(".//size"):
            sizes.append(
                {
                    "label": s.attrib["label"],
                    "width": int(s.attrib["width"]),
                    "height": int(s.attrib["height"]),
                    "media": s.attrib["media"],
                    "source": s.attrib["source"],
                }
            )

        # We have two options with tags: we can use the 'raw' version
        # entered by the user, or we can use the normalised version in
        # the tag text.
        #
        # e.g. "bay of bengal" vs "bayofbengal"
        #
        # We prefer the normalised version because it makes it possible
        # to compare tags across photos, and we only get the normalised
        # versions from the collection endpoints.
        tags_elem = find_required_elem(photo_elem, path="tags")

        tags = []
        for t in tags_elem.findall("tag"):
            assert t.text is not None
            tags.append(t.text)

        # The <location> tag is only present in photos which have
        # location data; if the user hasn't made location available to
        # public users, it'll be missing.
        #
        # The accuracy parameter in the Flickr API response tells us
        # the precision of the location information (15 November 2023):
        #
        #     Recorded accuracy level of the location information.
        #     World level is 1, Country is ~3, Region ~6, City ~11, Street ~16.
        #     Current range is 1-16.
        #
        # But some photos have an accuracy of 0!  It's unclear what this
        # means or how we should map this -- lower numbers mean less accurate,
        # so this location information might be completely useless.
        #
        # Discard it rather than risk writing bad data into Wikimedia.
        location_elem = photo_elem.find(path="location")

        location: LocationInfo | None

        if location_elem is not None and location_elem.attrib["accuracy"] != "0":
            location = {
                "latitude": float(location_elem.attrib["latitude"]),
                "longitude": float(location_elem.attrib["longitude"]),
                "accuracy": int(location_elem.attrib["accuracy"]),
            }
        else:
            location = None

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
            "original_format": original_format,
            "tags": tags,
            "location": location,
        }

    # There are a bunch of similar flickr.XXX.getPhotos methods;
    # these are some constants and utility methods to help when
    # calling them.
    extras = [
        "license",
        "date_upload",
        "date_taken",
        "media",
        "original_format",
        "owner_name",
        "url_sq",
        "url_t",
        "url_s",
        "url_m",
        "url_o",
        "tags",
        "geo",
        # These parameters aren't documented, but they're quite
        # useful for our purposes!
        "url_q",  # Large Square
        "url_l",  # Large
        "description",
        "safety_level",
        "realname",
    ]

    def _parse_collection_of_photos_response(
        self,
        elem: ET.Element,
        collection_owner: User | None = None,
    ) -> CollectionOfPhotos:
        # The wrapper element includes a couple of attributes related
        # to pagination, e.g.
        #
        #     <photoset pages="1" total="2" …>
        #
        page_count = int(elem.attrib["pages"])
        total_photos = int(elem.attrib["total"])

        photos: list[SinglePhoto] = []

        for photo_elem in elem.findall(".//photo"):
            photo_id = photo_elem.attrib["id"]

            title = photo_elem.attrib["title"] or None
            description = find_optional_text(photo_elem, path="description")

            tags = photo_elem.attrib["tags"].split()

            owner: User
            if collection_owner is None:
                owner_name = photo_elem.attrib["owner"]
                path_alias = photo_elem.attrib.get("pathalias") or None

                owner = {
                    "id": photo_elem.attrib["owner"],
                    "username": photo_elem.attrib["ownername"],
                    "realname": photo_elem.attrib.get("realname") or None,
                    "path_alias": path_alias,
                    "photos_url": f"https://www.flickr.com/photos/{path_alias or owner_name}/",
                    "profile_url": f"https://www.flickr.com/people/{path_alias or owner_name}/",
                }
            else:
                owner = collection_owner

            assert owner["photos_url"].endswith("/")
            url = owner["photos_url"] + photo_id + "/"

            # The lat/long/accuracy fields will always be populated, even
            # if there's no geo-information on this photo -- they're just
            # set to zeroes.
            #
            # We have to use the presence of geo permissions on the
            # <photo> element to determine if there's actually location
            # information here, or if we're getting the defaults.
            #
            # We discard location information with an accuracy of "0";
            # see comment in the ``get_single_photo()`` method for an
            # explanation of why this is so unhelpful as to be useless.
            location: LocationInfo | None

            if (
                photo_elem.attrib.get("geo_is_public") == "1"
                and photo_elem.attrib["accuracy"] != "0"
            ):
                location = {
                    "latitude": float(photo_elem.attrib["latitude"]),
                    "longitude": float(photo_elem.attrib["longitude"]),
                    "accuracy": int(photo_elem.attrib["accuracy"]),
                }
            else:
                location = None

            photos.append(
                {
                    "id": photo_id,
                    "title": title,
                    "description": description,
                    "date_posted": parse_date_posted(photo_elem.attrib["dateupload"]),
                    "date_taken": self._get_date_taken(
                        value=photo_elem.attrib["datetaken"],
                        granularity=photo_elem.attrib["datetakengranularity"],
                        unknown=photo_elem.attrib["datetakenunknown"] == "1",
                    ),
                    "license": self.lookup_license_by_id(
                        id=photo_elem.attrib["license"]
                    ),
                    "sizes": parse_sizes(photo_elem),
                    "original_format": photo_elem.attrib.get("originalformat"),
                    "safety_level": parse_safety_level(
                        photo_elem.attrib["safety_level"]
                    ),
                    "owner": owner,
                    "url": url,
                    "tags": tags,
                    "location": location,
                }
            )

        return {
            "page_count": page_count,
            "total_photos": total_photos,
            "photos": photos,
        }

    def get_photos_in_album(
        self, *, user_url: str, album_id: str, page: int = 1, per_page: int = 10
    ) -> PhotosInAlbum:
        """
        Get the photos in an album.
        """
        user = self.lookup_user_by_url(url=user_url)

        # https://www.flickr.com/services/api/flickr.photosets.getPhotos.html
        resp = self.call(
            method="flickr.photosets.getPhotos",
            params={
                "user_id": user["id"],
                "photoset_id": album_id,
                "extras": ",".join(self.extras),
                "page": str(page),
                "per_page": str(per_page),
            },
        )

        parsed_resp = self._parse_collection_of_photos_response(
            find_required_elem(resp, path=".//photoset"), collection_owner=user
        )

        # https://www.flickr.com/services/api/flickr.photosets.getInfo.html
        album_resp = self.call(
            method="flickr.photosets.getInfo",
            params={"user_id": user["id"], "photoset_id": album_id},
        )
        album_title = find_required_text(album_resp, path=".//title")

        return {
            "photos": parsed_resp["photos"],
            "page_count": parsed_resp["page_count"],
            "total_photos": parsed_resp["total_photos"],
            "album": {"owner": user, "title": album_title},
        }

    def get_photos_in_gallery(
        self, *, gallery_id: str, page: int = 1, per_page: int = 10
    ) -> PhotosInGallery:
        """
        Get the photos in a gallery.
        """
        # https://www.flickr.com/services/api/flickr.galleries.getPhotos.html
        resp = self.call(
            method="flickr.galleries.getPhotos",
            params={
                "gallery_id": gallery_id,
                "get_gallery_info": "1",
                "extras": ",".join(self.extras + ["path_alias"]),
                "page": str(page),
                "per_page": str(per_page),
            },
        )

        parsed_resp = self._parse_collection_of_photos_response(
            find_required_elem(resp, path=".//photos")
        )

        gallery_elem = find_required_elem(resp, path=".//gallery")

        gallery_title = find_required_text(gallery_elem, path="title")
        gallery_owner_name = gallery_elem.attrib["username"]

        return {
            "photos": parsed_resp["photos"],
            "page_count": parsed_resp["page_count"],
            "total_photos": parsed_resp["total_photos"],
            "gallery": {"owner_name": gallery_owner_name, "title": gallery_title},
        }

    def get_public_photos_by_user(
        self, user_url: str, page: int = 1, per_page: int = 10
    ) -> CollectionOfPhotos:
        """
        Get all the public photos by a user on Flickr.
        """
        user = self.lookup_user_by_url(url=user_url)

        # See https://www.flickr.com/services/api/flickr.people.getPublicPhotos.html
        photos_resp = self.call(
            method="flickr.people.getPublicPhotos",
            params={
                "user_id": user["id"],
                "extras": ",".join(self.extras),
                "page": str(page),
                "per_page": str(per_page),
            },
        )

        return self._parse_collection_of_photos_response(
            find_required_elem(photos_resp, path=".//photos"), collection_owner=user
        )

    def lookup_group_from_url(self, *, url: str) -> GroupInfo:
        """
        Given the link to a group's photos or profile, return some info.
        """
        resp = self.call(method="flickr.urls.lookupGroup", params={"url": url})

        # The lookupUser response is of the form:
        #
        #       <group id="34427469792@N01">
        #         <groupname>FlickrCentral</groupname>
        #       </group>
        #
        group_elem = find_required_elem(resp, path=".//group")

        return {
            "id": group_elem.attrib["id"],
            "name": find_required_text(group_elem, path="groupname"),
        }

    def get_photos_in_group_pool(
        self, group_url: str, page: int = 1, per_page: int = 10
    ) -> PhotosInGroup:
        """
        Get all the photos in a group pool.
        """
        group_info = self.lookup_group_from_url(url=group_url)

        # See https://www.flickr.com/services/api/flickr.groups.pools.getPhotos.html
        photos_resp = self.call(
            method="flickr.groups.pools.getPhotos",
            params={
                "group_id": group_info["id"],
                "extras": ",".join(self.extras),
                "page": str(page),
                "per_page": str(per_page),
            },
        )

        parsed_resp = self._parse_collection_of_photos_response(
            find_required_elem(photos_resp, path=".//photos")
        )

        return {
            "photos": parsed_resp["photos"],
            "page_count": parsed_resp["page_count"],
            "total_photos": parsed_resp["total_photos"],
            "group": group_info,
        }

    def get_photos_with_tag(
        self, tag: str, page: int = 1, per_page: int = 10
    ) -> CollectionOfPhotos:
        """
        Get all the photos that use a given tag.
        """
        resp = self.call(
            method="flickr.photos.search",
            params={
                "tags": tag,
                # This is so we get the same photos as you see on the "tag" page
                # under "All Photos Tagged XYZ" -- if you click the URL to the
                # full search results, you end up on a page like:
                #
                #     https://flickr.com/search/?sort=interestingness-desc&…
                #
                "sort": "interestingness-desc",
                "extras": ",".join(self.extras),
                "page": str(page),
                "per_page": str(per_page),
            },
        )

        return self._parse_collection_of_photos_response(
            find_required_elem(resp, path=".//photos")
        )
