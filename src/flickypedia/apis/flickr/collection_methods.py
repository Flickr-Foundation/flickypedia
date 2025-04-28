"""
Methods for getting information about collections of photos in Flickr
(albums, galleries, groups, and so on).
"""

from xml.etree import ElementTree as ET

from nitrate.xml import find_optional_text, find_required_elem, find_required_text
from flickr_photos_api import FlickrApi
from flickr_photos_api.date_parsers import parse_date_taken, parse_timestamp
from flickr_photos_api.exceptions import ResourceNotFound
from flickr_photos_api.types import User, create_user, get_machine_tags
from flickr_photos_api.utils import parse_location, parse_safety_level, parse_sizes

from flickypedia.types.flickr import (
    CollectionOfPhotos,
    FlickrPhoto,
    GroupInfo,
    PhotosInAlbum,
    PhotosInGallery,
    PhotosInGroup,
)


def _from_collection_photo(
    api: FlickrApi, photo_elem: ET.Element, owner: User | None
) -> FlickrPhoto:
    """
    Given a <photo> element from a collection response, extract all the photo info.
    """
    photo_id = photo_elem.attrib["id"]

    original_format = photo_elem.attrib.get("originalformat")

    if owner is None:
        owner = create_user(
            user_id=photo_elem.attrib["owner"],
            username=photo_elem.attrib["ownername"],
            realname=photo_elem.attrib.get("realname"),
            path_alias=photo_elem.attrib["pathalias"],
        )

    assert owner is not None

    safety_level = parse_safety_level(photo_elem.attrib["safety_level"])

    license = api.lookup_license_by_id(id=photo_elem.attrib["license"])

    title = photo_elem.attrib["title"] or None
    description = find_optional_text(photo_elem, path="description")
    tags = photo_elem.attrib["tags"].split()

    date_posted = parse_timestamp(photo_elem.attrib["dateupload"])
    date_taken = parse_date_taken(
        value=photo_elem.attrib["datetaken"],
        granularity=photo_elem.attrib["datetakengranularity"],
        unknown=photo_elem.attrib["datetakenunknown"] == "1",
    )

    # The lat/long/accuracy fields will always be populated, even
    # if there's no geo-information on this photo -- they're just
    # set to zeroes.
    #
    # We have to use the presence of geo permissions on the
    # <photo> element to determine if there's actually location
    # information here, or if we're getting the defaults.
    if photo_elem.attrib.get("geo_is_public") == "1":
        location = parse_location(photo_elem)
    else:
        location = None

    assert owner["photos_url"].endswith("/")
    url = owner["photos_url"] + photo_id + "/"

    sizes = parse_sizes(photo_elem)

    return {
        "id": photo_id,
        "title": title,
        "description": description,
        "owner": owner,
        "date_taken": date_taken,
        "date_posted": date_posted,
        "location": location,
        "license": license,
        "sizes": sizes,
        "tags": tags,
        "machine_tags": get_machine_tags(tags),
        "safety_level": safety_level,
        "url": url,
        "original_format": original_format,
    }


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
    "path_alias",
    "count_comments",
    "count_views",
]


def _create_collection(
    api: FlickrApi, collection_elem: ET.Element, owner: User | None = None
) -> CollectionOfPhotos:
    """
    This gets pagination information and extracts individual <photo>
    elements from a collection response.
    """
    photos = [
        _from_collection_photo(api, photo_elem, owner=owner)
        for photo_elem in collection_elem.findall("photo")
    ]

    # The wrapper element includes a couple of attributes related
    # to pagination, e.g.
    #
    #     <photoset pages="1" total="2" …>
    #
    count_pages = int(collection_elem.attrib["pages"])
    count_photos = int(collection_elem.attrib["total"])

    return {
        "photos": photos,
        "count_pages": count_pages,
        "count_photos": count_photos,
    }


def get_photos_in_album(
    api: FlickrApi,
    album_id: str,
    user_id: str | None = None,
    user_url: str | None = None,
    page: int = 1,
    per_page: int = 10,
) -> PhotosInAlbum:
    """
    Get a page of photos from an album.

    You need to pass a numeric album ID and one of the ``user_id`` or ``user_url``.

    For example, if the album URL is

        https://www.flickr.com/photos/158685238@N03/albums/72177720313849533/

    then you need to pass one of:

        {"album_id": "72177720313849533", "user_id": "158685238@N03"}
        {"album_id": "72177720313849533", "user_url": "https://www.flickr.com/photos/158685238@N03/"}

    """
    user_id = api._ensure_user_id(user_id=user_id, user_url=user_url)

    return _get_photos_in_album(
        api, user_id=user_id, album_id=album_id, page=page, per_page=per_page
    )


def _get_photos_in_album(
    api: FlickrApi, *, user_id: str, album_id: str, page: int, per_page: int
) -> PhotosInAlbum:
    """
    Get a page of photos from an album.
    """
    # https://www.flickr.com/services/api/flickr.photosets.getPhotos.html
    resp = api.call(
        method="flickr.photosets.getPhotos",
        params={
            "user_id": user_id,
            "photoset_id": album_id,
            "extras": ",".join(extras),
            "page": page,
            "per_page": per_page,
        },
        exceptions={
            "1": ResourceNotFound(f"Could not find album with ID: {album_id!r}"),
            "2": ResourceNotFound(f"Could not find user with ID: {user_id!r}"),
        },
    )

    # Albums are always non-empty, so we know we'll find something here
    photoset_elem = find_required_elem(resp, path="photoset")
    photo_elem = find_required_elem(photoset_elem, path="photo")

    owner = create_user(
        user_id=photoset_elem.attrib["owner"],
        username=photoset_elem.attrib["ownername"],
        realname=photo_elem.attrib.get("realname"),
        path_alias=photo_elem.attrib["pathalias"],
    )

    album_title = photoset_elem.attrib["title"]

    return {
        **_create_collection(api, photoset_elem, owner=owner),
        "album": {
            "owner": owner,
            "title": album_title,
        },
    }


def get_photos_in_gallery(
    api: FlickrApi, *, gallery_id: str, page: int = 1, per_page: int = 10
) -> PhotosInGallery:
    """
    Get a page of photos in a gallery.
    """
    # https://www.flickr.com/services/api/flickr.galleries.getPhotos.html
    resp = api.call(
        method="flickr.galleries.getPhotos",
        params={
            "gallery_id": gallery_id,
            "get_gallery_info": "1",
            "extras": ",".join(extras),
            "page": page,
            "per_page": per_page,
        },
        exceptions={
            "1": ResourceNotFound(f"Could not find gallery with ID: {gallery_id!r}")
        },
    )

    gallery_elem = find_required_elem(resp, path="gallery")

    gallery_title = find_required_text(gallery_elem, path="title")
    gallery_owner_name = gallery_elem.attrib["username"]

    photos_elem = find_required_elem(resp, path="photos")

    return {
        **_create_collection(api, photos_elem),
        "gallery": {"owner_name": gallery_owner_name, "title": gallery_title},
    }


def get_photos_in_user_photostream(
    api: FlickrApi,
    user_id: str | None = None,
    user_url: str | None = None,
    page: int = 1,
    per_page: int = 10,
) -> CollectionOfPhotos:
    """
    Get a page of photos from a user's photostream.

    You need to pass either the ``user_id`` or ``user_url``.

    For example, if the person's URL is

        https://www.flickr.com/photos/158685238@N03/

    then you need to pass one of:

        {"user_id": "158685238@N03"}
        {"user_url": "https://www.flickr.com/photos/158685238@N03/"}

    """
    user_id = api._ensure_user_id(user_id=user_id, user_url=user_url)

    # See https://www.flickr.com/services/api/flickr.people.getPublicPhotos.html
    resp = api.call(
        method="flickr.people.getPublicPhotos",
        params={
            "user_id": user_id,
            "extras": ",".join(extras),
            "page": page,
            "per_page": per_page,
        },
        exceptions={"1": ResourceNotFound(f"Could not find user with ID: {user_id!r}")},
    )

    first_photo = resp.find(".//photo")

    # The user hasn't uploaded any photos
    if first_photo is None:
        return {"count_pages": 1, "count_photos": 0, "photos": []}

    owner = create_user(
        user_id=first_photo.attrib["owner"],
        username=first_photo.attrib["ownername"],
        realname=first_photo.attrib.get("realname"),
        path_alias=first_photo.attrib["pathalias"],
    )

    photos_elem = find_required_elem(resp, path="photos")

    return _create_collection(api, photos_elem, owner=owner)


def _lookup_group_from_url(api: FlickrApi, *, url: str) -> GroupInfo:
    """
    Given the link to a group's photos or profile, return some info.
    """
    # See https://www.flickr.com/services/api/flickr.urls.lookupGroup.html
    resp = api.call(
        method="flickr.urls.lookupGroup",
        params={"url": url},
        exceptions={"1": ResourceNotFound(f"Could not find group with URL: {url!r}")},
    )

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
    api: FlickrApi, *, group_url: str, page: int = 1, per_page: int = 10
) -> PhotosInGroup:
    """
    Get a page of photos in a group pool.
    """
    group_info = _lookup_group_from_url(api, url=group_url)

    # See https://www.flickr.com/services/api/flickr.groups.pools.getPhotos.html
    resp = api.call(
        method="flickr.groups.pools.getPhotos",
        params={
            "group_id": group_info["id"],
            "extras": ",".join(extras),
            "page": page,
            "per_page": per_page,
        },
    )

    photos_elem = find_required_elem(resp, path="photos")

    return {
        **_create_collection(api, photos_elem),
        "group": group_info,
    }


def get_photos_with_tag(
    api: FlickrApi, *, tag: str, page: int = 1, per_page: int = 10
) -> CollectionOfPhotos:
    """
    Get a page of photos in a tag.

    Note that tag pagination and ordering results can be inconsistent,
    especially for large tags -- it's tricky to do an "exhaustive" search
    of a Flickr tag.
    """
    resp = api.call(
        method="flickr.photos.search",
        params={
            "tags": tag,
            "page": page,
            "per_page": per_page,
            # This is so we get the same photos as you see on the "tag" page
            # under "All Photos Tagged XYZ" -- if you click the URL to the
            # full search results, you end up on a page like:
            #
            #     https://flickr.com/search/?sort=interestingness-desc&…
            #
            "sort": "interestingness-desc",
            "extras": ",".join(extras),
        },
    )

    photos_elem = find_required_elem(resp, path="photos")

    return _create_collection(api, photos_elem)
