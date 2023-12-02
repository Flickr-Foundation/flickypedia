from .api import FlickrPhotosApi
from .exceptions import FlickrApiException, ResourceNotFound, LicenseNotFound
from ._types import (
    License,
    User,
    TakenGranularity,
    DateTaken,
    LocationInfo,
    Size,
    SafetyLevel,
    SinglePhoto,
    CollectionOfPhotos,
    PhotosFromUrl,
    PhotosInAlbum,
    PhotosInGallery,
    PhotosInGroup,
    AlbumInfo,
    GalleryInfo,
    GroupInfo,
)


__version__ = "1.3.1"


__all__ = [
    "FlickrPhotosApi",
    "FlickrApiException",
    "ResourceNotFound",
    "LicenseNotFound",
    "License",
    "LocationInfo",
    "User",
    "TakenGranularity",
    "DateTaken",
    "Size",
    "SafetyLevel",
    "SinglePhoto",
    "CollectionOfPhotos",
    "PhotosFromUrl",
    "PhotosInAlbum",
    "PhotosInGallery",
    "PhotosInGroup",
    "AlbumInfo",
    "GalleryInfo",
    "GroupInfo",
    "__version__",
]
