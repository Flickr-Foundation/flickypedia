import pathlib
from typing import Dict, List, Literal, TypedDict, Union
import uuid

from flask import current_app
from flask_login import current_user
from flickr_photos_api import SinglePhoto
import httpx
import keyring

from flickypedia.apis.structured_data import NewClaims
from flickypedia.apis.wikimedia import ShortCaption, WikimediaApi
from flickypedia.apis.wikitext import create_wikitext
from flickypedia.duplicates import record_file_created_by_flickypedia
from flickypedia.photos import size_at
from flickypedia.uploadr.fs_queue import AbstractFilesystemTaskQueue


# Types for upload requests.


class UploadRequest(TypedDict):
    photo: SinglePhoto
    sdc: NewClaims
    title: str
    caption: ShortCaption
    categories: list[str]


class UploadBatch(TypedDict):
    keyring_id: str
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


UploadBatchResults = Dict[str, Union[SuccessfulUpload, FailedUpload, PendingUpload]]


class PhotoUploadQueue(AbstractFilesystemTaskQueue[UploadBatch, UploadBatchResults]):
    def process_individual_task(self, task: UploadBatch) -> None:
        print(task["id"])

        q.record_task_event(
            task, state="in_progress", event="Starting to upload photos"
        )

        keyring_id = task["task_input"]["keyring_id"]

        # Read the access token from the system keychain, then immediately
        # purge it.  This ensures that the access token is single use,
        # and can't be reused later.
        access_token = keyring.get_password("flickypedia", keyring_id)
        keyring.delete_password("flickypedia", keyring_id)

        client = httpx.Client(headers={"Authorization": f"Bearer {access_token}"})
        api = WikimediaApi(client=client)

        for upload_request in task["task_input"]["requests"]:
            photo_id = upload_request["photo"]["id"]

            task["task_output"][photo_id] = {"state": "in_progress"}
            q.record_task_event(task, event=f"Uploading photo {photo_id}")

            try:
                upload_result = upload_single_image(api, upload_request)
            except Exception as exc:
                task["task_output"][photo_id] = {
                    "state": "failed",
                    "error": str(exc),
                }
            else:
                task["task_output"][photo_id] = {
                    "state": "succeeded",
                    "id": upload_result["id"],
                    "title": upload_result["title"],
                }

            q.record_task_event(
                task,
                event=f"Finished photo {photo_id} ({task['task_output'][photo_id]['state']})",
            )


def begin_upload(upload_requests: List[UploadRequest]) -> str:
    """
    Trigger an upload task to run in the background.
    """
    q = uploads_queue()

    upload_id = str(uuid.uuid4())

    # Get a fresh token for the user, so we know we have the full
    # four hours before the access token expires.
    #
    # We store this token in the system keychain -- this allows us
    # to pass it securely between processes without it being saved
    # in plaintext on the disk.
    current_user.refresh_token()

    keyring_id = f"user-{current_user.id}-id-{upload_id}"
    keyring.set_password(
        "flickypedia", keyring_id, password=current_user.token()["access_token"]
    )

    task_input = {"keyring_id": keyring_id, "requests": upload_requests}

    task_output = {req["photo"]["id"]: {"state": "waiting"} for req in upload_requests}

    q.start_task(task_input=task_input, task_output=task_output, task_id=upload_id)

    return upload_id


def upload_single_image(api: WikimediaApi, request: UploadRequest) -> SuccessfulUpload:
    """
    Upload a photo from Flickr to Wikimedia Commons.

    This includes:

    -   Copying the photo from Flickr to Wikimedia Commons
    -   Adding the file caption supplied by the user
    -   Adding the structured data to the photo

    """
    wikitext = create_wikitext(license_id=request["photo"]["license"]["id"])

    original_size = size_at(request["photo"]["sizes"], desired_size="Original")

    wikimedia_page_title = api.upload_image(
        filename=request["title"], original_url=original_size["source"], text=wikitext
    )

    wikimedia_page_id = api.add_file_caption(
        filename=request["title"], caption=request["caption"]
    )

    api.add_structured_data(filename=request["title"], data=request["sdc"])

    # Now we add the categories to the Wikitext.
    #
    # It might seem strange to add these separately, when we could add
    # the text as part of the initial upload -- but what we're doing
    # here is forcing a re-render of the Lua-driven {{Information}}
    # template in the Wikitext.
    #
    # It's populated by the structured data, but that structured data
    # wasn't present for the initial upload, so the template appears
    # empty.  It's not until the text changes that it gets filled in
    # with the SDC.
    api.add_categories_to_page(
        filename=request["title"], categories=request["categories"]
    )

    wikimedia_page_title = f"File:{wikimedia_page_title}"

    record_file_created_by_flickypedia(
        flickr_photo_id=request["photo"]["id"],
        wikimedia_page_title=wikimedia_page_title,
        wikimedia_page_id=wikimedia_page_id,
    )

    return {"id": wikimedia_page_id, "title": wikimedia_page_title}


def uploads_queue() -> PhotoUploadQueue:
    """
    Return an instance of the PhotoUploadQueue that's tied to the
    current Flask app.
    """
    return PhotoUploadQueue(base_dir=current_app.config["UPLOAD_QUEUE_DIRECTORY"])


if __name__ == "__main__":
    from flickypedia.uploadr import create_app

    app = create_app(data_directory=pathlib.Path("data"))

    with app.app_context():
        q = PhotoUploadQueue(base_dir=pathlib.Path("queue/uploads"))
        q.process_single_task()
