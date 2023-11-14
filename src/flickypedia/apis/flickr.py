"""
Get a collection of photos from Flickr.

We record when we call the Flickr API, because that information will
later be saved as part of the SDC on Wikimedia.
"""

import datetime
from typing import List, TypedDict, Union

from flask import current_app
from flickr_photos_api import (
    CollectionOfPhotos,
    FlickrPhotosApi,
    PhotosInAlbum,
    PhotosInGallery,
    PhotosInGroup,
    SinglePhoto,
    User as FlickrUser,
)
from flickr_url_parser import ParseResult


class RetrievedAtMixin(TypedDict):
    retrieved_at: datetime.datetime


class SinglePhotoData(TypedDict, RetrievedAtMixin):
    photos: List[SinglePhoto]
    owner: FlickrUser


class CollectionsOfPhotoData(CollectionOfPhotos, RetrievedAtMixin):
    pass


class PhotosInAlbumData(PhotosInAlbum, RetrievedAtMixin):
    pass


class PhotosInGalleryData(PhotosInGallery, RetrievedAtMixin):
    pass


class PhotosInGroupData(PhotosInGroup, RetrievedAtMixin):
    pass


class PhotosInUserPhotostreamData(CollectionsOfPhotoData):
    owner: FlickrUser


GetPhotosData = Union[
    SinglePhotoData,
    CollectionsOfPhotoData,
    PhotosInAlbumData,
    PhotosInGalleryData,
    PhotosInGroupData,
    PhotosInUserPhotostreamData,
]


def get_photos_from_flickr(parsed_url: ParseResult) -> GetPhotosData:
    """
    Get a collection of photos from Flickr.
    """
    retrieved_at = datetime.datetime.now()

    api = FlickrPhotosApi(
        api_key=current_app.config["FLICKR_API_KEY"],
        user_agent=current_app.config["USER_AGENT"],
    )

    if parsed_url["type"] == "single_photo":
        photo = api.get_single_photo(photo_id=parsed_url["photo_id"])

        return {
            "photos": [photo],
            "owner": photo["owner"],
            "retrieved_at": retrieved_at,
        }

    elif parsed_url["type"] == "album":
        album_resp = api.get_photos_in_album(
            user_url=parsed_url["user_url"],
            album_id=parsed_url["album_id"],
            page=parsed_url["page"],
            per_page=100,
        )

        return {**album_resp, "retrieved_at": retrieved_at}

    elif parsed_url["type"] == "user":
        user_resp = api.get_public_photos_by_user(
            user_url=parsed_url["user_url"], page=parsed_url["page"], per_page=100
        )

        return {
            **user_resp,
            "owner": user_resp["photos"][0]["owner"],
            "retrieved_at": retrieved_at,
        }
    elif parsed_url["type"] == "gallery":
        gallery_resp = api.get_photos_in_gallery(
            gallery_id=parsed_url["gallery_id"],
            page=parsed_url["page"],
            per_page=100,
        )

        return {**gallery_resp, "retrieved_at": retrieved_at}
    elif parsed_url["type"] == "group":
        group_resp = api.get_photos_in_group_pool(
            group_url=parsed_url["group_url"], page=parsed_url["page"], per_page=100
        )

        return {**group_resp, "retrieved_at": retrieved_at}
    elif parsed_url["type"] == "tag":
        tag_resp = api.get_photos_with_tag(
            tag=parsed_url["tag"], page=parsed_url["page"], per_page=100
        )

        return {**tag_resp, "retrieved_at": retrieved_at}
    else:  # pragma: no cover
        raise TypeError(f"Unrecognised URL type: {parsed_url['type']}")
