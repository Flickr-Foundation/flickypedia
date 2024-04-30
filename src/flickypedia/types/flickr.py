import datetime
import typing

from flickr_photos_api import (
    SinglePhoto,
    CollectionOfPhotos,
    PhotosInAlbum,
    PhotosInGallery,
    PhotosInGroup,
    User,
)


class RetrievedAtMixin(typing.TypedDict):
    retrieved_at: datetime.datetime


class SinglePhotoData(RetrievedAtMixin):
    photos: list[SinglePhoto]
    owner: User


class CollectionsOfPhotoData(CollectionOfPhotos, RetrievedAtMixin):
    pass


class PhotosInAlbumData(PhotosInAlbum, RetrievedAtMixin):
    pass


class PhotosInGalleryData(PhotosInGallery, RetrievedAtMixin):
    pass


class PhotosInGroupData(PhotosInGroup, RetrievedAtMixin):
    pass


class PhotosInUserPhotostreamData(CollectionsOfPhotoData):
    owner: User


GetPhotosData = (
    SinglePhotoData
    | CollectionsOfPhotoData
    | PhotosInAlbumData
    | PhotosInGalleryData
    | PhotosInGroupData
    | PhotosInUserPhotostreamData
)
