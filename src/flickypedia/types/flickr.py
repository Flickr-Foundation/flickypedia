from datetime import datetime
import typing

from flickr_api.models import (
    DateTaken,
    License,
    LocationInfo,
    MachineTags,
    SafetyLevel,
    Size,
    User,
)


class FlickrPhoto(typing.TypedDict):
    """
    All the information we need about a photo in Flickypedia.
    """

    id: str
    title: str | None
    description: str | None
    owner: User
    date_taken: DateTaken | None
    date_posted: datetime
    location: LocationInfo | None
    license: License
    sizes: list[Size]
    tags: list[str]
    machine_tags: MachineTags
    safety_level: SafetyLevel
    url: str
    original_format: str | None


class CollectionOfPhotos(typing.TypedDict):
    photos: list[FlickrPhoto]

    # Note: there are no parameters named like this in the Flickr API;
    # these names were chosen to match parameters that do exist like
    # `count_views` or `count_comments`.
    count_pages: int
    count_photos: int


class AlbumInfo(typing.TypedDict):
    owner: User
    title: str


class PhotosInAlbum(CollectionOfPhotos):
    album: AlbumInfo


class GalleryInfo(typing.TypedDict):
    owner_name: str
    title: str


class PhotosInGallery(CollectionOfPhotos):
    gallery: GalleryInfo


class GroupInfo(typing.TypedDict):
    id: str
    name: str


class PhotosInGroup(CollectionOfPhotos):
    group: GroupInfo


class RetrievedAtMixin(typing.TypedDict):
    retrieved_at: datetime


class SinglePhotoData(RetrievedAtMixin):
    photos: list[FlickrPhoto]
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
