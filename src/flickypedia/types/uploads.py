import typing

from flickr_photos_api import SinglePhoto

from flickypedia.types.structured_data import NewClaims
from flickypedia.types.wikimedia import ShortCaption


# Types for upload requests.


class UploadRequest(typing.TypedDict):
    photo: SinglePhoto
    sdc: NewClaims
    title: str
    caption: ShortCaption
    categories: list[str]
    username: str


class KeyringId(typing.TypedDict):
    service_name: str
    username: str


class UploadBatch(typing.TypedDict):
    keyring_id: KeyringId
    requests: list[UploadRequest]


# Types for upload results.


class SuccessfulUpload(typing.TypedDict):
    id: str
    title: str
    state: typing.Literal["succeeded"]


class FailedUpload(typing.TypedDict):
    state: typing.Literal["failed"]
    error: str


class PendingUpload(typing.TypedDict):
    state: typing.Literal["waiting", "in_progress"]


IndividualUploadResult = SuccessfulUpload | FailedUpload | PendingUpload

UploadBatchResults = dict[str, IndividualUploadResult]
