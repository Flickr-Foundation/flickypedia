from typing import Literal, TypedDict

from flickr_photos_api import SinglePhoto

from flickypedia.types.structured_data import NewClaims
from flickypedia.types.wikimedia import ShortCaption


# Types for upload requests.


class UploadRequest(TypedDict):
    photo: SinglePhoto
    sdc: NewClaims
    title: str
    caption: ShortCaption
    categories: list[str]
    username: str


class KeyringId(TypedDict):
    service_name: str
    username: str


class UploadBatch(TypedDict):
    keyring_id: KeyringId
    requests: list[UploadRequest]


# Types for upload results.


class SuccessfulUpload(TypedDict):
    id: str
    title: str
    state: Literal["succeeded"]


class FailedUpload(TypedDict):
    state: Literal["failed"]
    error: str


class PendingUpload(TypedDict):
    state: Literal["waiting", "in_progress"]


IndividualUploadResult = SuccessfulUpload | FailedUpload | PendingUpload

UploadBatchResults = dict[str, IndividualUploadResult]
