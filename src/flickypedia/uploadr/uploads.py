"""
Manage the process of uploading photos to Wikimedia.
"""

import functools
import uuid

from flask import current_app
from flask_login import current_user
import httpx
import keyring

from flickypedia.apis.wikimedia import WikimediaApi
from flickypedia.apis.wikitext import create_wikitext
from flickypedia.duplicates import record_file_created_by_flickypedia
from flickypedia.photos import size_at
from flickypedia.types.uploads import (
    KeyringId,
    SuccessfulUpload,
    UploadBatch,
    UploadBatchResults,
    UploadRequest,
)
from flickypedia.uploadr.fs_queue import AbstractFilesystemTaskQueue, Task


class PhotoUploadQueue(AbstractFilesystemTaskQueue[UploadBatch, UploadBatchResults]):
    """
    A task queue for uploading photos.

    The ``task_input`` contains:

    -   A keyring ID which can be used to retrieve the OAuth access token
        for this user.

    """

    def process_individual_task(
        self,
        task: Task[UploadBatch, UploadBatchResults],
    ) -> None:
        self.record_task_event(
            task, state="in_progress", event="Starting to upload photos"
        )

        keyring_id = task["task_input"]["keyring_id"]

        # Read the access token from the system keychain, then immediately
        # purge it.  This ensures that the access token is single use,
        # and can't be reused later.
        access_token = keyring.get_password(**keyring_id)
        keyring.delete_password(**keyring_id)

        client = httpx.Client(headers={"Authorization": f"Bearer {access_token}"})
        api = WikimediaApi(client=client)

        # Now go through the upload requests one-by-one.
        for upload_request in task["task_input"]["requests"]:
            photo_id = upload_request["photo"]["id"]

            task["task_output"][photo_id] = {"state": "in_progress"}
            self.record_task_event(task, event=f"Uploading photo {photo_id}")

            try:
                upload_result = self.upload_single_photo(api, upload_request)
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

            self.record_task_event(
                task,
                event=f"Finished photo {photo_id} ({task['task_output'][photo_id]['state']})",
            )

    def upload_single_photo(
        self, api: WikimediaApi, request: UploadRequest
    ) -> SuccessfulUpload:
        # This is a thin shim around the ``upload_single_photo`` function
        # that allows us to mock it for testing.
        return upload_single_photo(api, request)


def begin_upload(upload_requests: list[UploadRequest]) -> str:
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
    keyring_id: KeyringId = {
        "service_name": "flickypedia.user",
        "username": f"user-{current_user.id}-id-{upload_id}",
    }

    if not current_app.config["TESTING"]:
        current_user.refresh_token()
        keyring.set_password(
            **keyring_id, password=current_user.token()["access_token"]
        )

    task_input: UploadBatch = {"keyring_id": keyring_id, "requests": upload_requests}

    task_output: UploadBatchResults = {
        req["photo"]["id"]: {"state": "waiting"} for req in upload_requests
    }

    q.start_task(task_input=task_input, task_output=task_output, task_id=upload_id)

    return upload_id


def upload_single_photo(api: WikimediaApi, request: UploadRequest) -> SuccessfulUpload:
    """
    Upload a photo from Flickr to Wikimedia Commons.

    This includes:

    -   Copying the photo from Flickr to Wikimedia Commons
    -   Adding the file caption supplied by the user
    -   Adding the structured data to the photo

    """
    wikitext = create_wikitext(
        photo=request["photo"],
        wikimedia_username=request["username"],
        new_categories=request["categories"],
    )

    original_size = size_at(request["photo"]["sizes"], desired_size="Original")

    wikimedia_page_title = api.upload_image(
        filename=request["title"], original_url=original_size["source"], text=wikitext
    )

    wikimedia_page_id = api.add_file_caption(
        filename=request["title"], caption=request["caption"]
    )

    api.add_structured_data(
        filename=request["title"],
        data=request["sdc"],
        summary="Flickypedia edit (add structured data statements)",
    )
    api.purge_wikitext(filename=request["title"])

    wikimedia_page_title = f"File:{wikimedia_page_title}"

    record_file_created_by_flickypedia(
        flickr_photo_id=request["photo"]["id"],
        wikimedia_page_title=wikimedia_page_title,
        wikimedia_page_id=wikimedia_page_id,
    )

    return {
        "id": wikimedia_page_id,
        "title": wikimedia_page_title,
        "state": "succeeded",
    }


@functools.cache
def uploads_queue() -> PhotoUploadQueue:
    """
    Return an instance of the PhotoUploadQueue that's tied to the
    current Flask app.
    """
    return PhotoUploadQueue(base_dir=current_app.config["UPLOAD_QUEUE_DIRECTORY"])
