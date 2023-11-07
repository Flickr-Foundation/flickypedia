"""
Some methods for working with collections of photos.
"""

from typing import List, TypedDict, Union

from flask import current_app
from flickr_photos_api import (
    FlickrPhotosApi,
    PhotosInAlbum,
    PhotosInGallery,
    SinglePhoto,
    Size,
    User as FlickrUser,
)
from flickr_url_parser import ParseResult


class SinglePhotoData(TypedDict):
    photos: List[SinglePhoto]
    owner: FlickrUser


GetPhotosData = Union[SinglePhotoData, PhotosInAlbum, PhotosInGallery]


def get_photos_from_flickr(parse_result: ParseResult) -> GetPhotosData:
    """
    Given a correctly parsed URL, get a list of photos from the Flickr API.

    Note: this doesn't do any checking of the URLs for correct license,
    duplicates on Wikimedia Commons, etc.  It just returns a list of
    photos which can be found on Flickr.
    """
    api = FlickrPhotosApi(
        api_key=current_app.config["FLICKR_API_KEY"],
        user_agent=current_app.config["USER_AGENT"],
    )

    if parse_result["type"] == "single_photo":
        photo = api.get_single_photo(photo_id=parse_result["photo_id"])
        return {"photos": [photo], "owner": photo["owner"]}
    elif parse_result["type"] == "album":
        return api.get_photos_in_album(
            user_url=parse_result["user_url"],
            album_id=parse_result["album_id"],
            per_page=current_app.config["PHOTOS_PER_PAGE"],
        )
    elif parse_result["type"] == "gallery":
        return api.get_photos_in_gallery(
            gallery_id=parse_result["gallery_id"],
            per_page=current_app.config["PHOTOS_PER_PAGE"],
        )
    else:  # pragma: no cover
        raise TypeError


def size_at(sizes: List[Size], *, desired_size: str) -> Size:
    """
    Given a list of sizes of Flickr photo, return the info about
    the desired size.
    """
    sizes_by_label = {s["label"]: s for s in sizes}

    # Flickr has a published list of possible sizes here:
    # https://www.flickr.com/services/api/misc.urls.html
    #
    # If the desired size isn't available, that means one of two things:
    #
    #   1.  The owner of this photo has done something to restrict downloads
    #       of their photo beyond a certain size.  But CC-licensed photos
    #       are always available to download, so that's not an issue for us.
    #   2.  This photo is smaller than the size we've asked for, in which
    #       case we fall back to Original as the largest possible size.
    #
    try:
        return sizes_by_label[desired_size]
    except KeyError:
        return sizes_by_label["Original"]
