import datetime
from typing import Any, List, TypedDict
import uuid

from celery import current_task, shared_task
from flask import current_app
from flask_login import current_user
from flickr_photos_api import SinglePhoto
import httpx

from flickypedia.apis._types import Statement
from flickypedia.apis.wikimedia import ShortCaption, WikimediaApi
from flickypedia.apis.wikitext import create_wikitext
from flickypedia.duplicates import record_file_created_by_flickypedia
from flickypedia.photos import size_at
from flickypedia.tasks import ProgressTracker


class UploadRequest(TypedDict):
    photo: SinglePhoto
    sdc: List[Statement]
    title: str
    caption: ShortCaption
    categories: List[str]


def begin_upload(upload_requests: List[UploadRequest]) -> str:
    """
    Trigger an upload task to run in the background.
    """
    task_id = str(uuid.uuid4())

    # Start by recording some progress data about the request -- this
    # will allow us to render a progress screen immediately.
    tracker = ProgressTracker(task_id=task_id)
    progress_data = [
        {"req": req, "last_update": datetime.datetime.now(), "status": "waiting"}
        for req in upload_requests
    ]
    tracker.record_progress(data=progress_data)

    # Get a fresh token for the user, so we know we have the full
    # four hours before the access token expires.
    current_user.refresh_token()

    upload_batch_of_photos.apply_async(  # type: ignore
        kwargs={
            "access_token": current_user.token()["access_token"],
            "upload_requests": upload_requests,
        },
        task_id=task_id,
    )

    return task_id


@shared_task
def upload_batch_of_photos(
    access_token: str, upload_requests: List[UploadRequest]
) -> Any:
    tracker = ProgressTracker(task_id=current_task.request.id)
    progress_data = tracker.get_progress()

    client = httpx.Client(
        headers={
            "Authorization": f"Bearer {access_token}",
            "User-Agent": current_app.config["USER_AGENT"],
        }
    )

    api = WikimediaApi(client=client)  # noqa

    for idx, req in enumerate(upload_requests):
        progress_data[idx]["status"] = "in_progress"
        tracker.record_progress(data=progress_data)

        try:
            progress_data[idx]["upload_result"] = upload_single_image(api, req)
        except Exception as exc:
            progress_data[idx]["status"] = "failed"
            progress_data[idx]["error"] = str(exc)
        else:
            progress_data[idx]["status"] = "succeeded"

        tracker.record_progress(data=progress_data)

    return progress_data


class UploadResult(TypedDict):
    id: str
    title: str


def upload_single_image(api: WikimediaApi, request: UploadRequest) -> UploadResult:
    """
    Upload a photo from Flickr to Wikimedia Commons.

    This includes:

    -   Copying the photo from Flickr to Wikimedia Commons
    -   Adding the file caption supplied by the user
    -   Adding the structured data to the photo

    """

    wikitext = create_wikitext(
        license_id=request["photo"]["license"]["id"], categories=request["categories"]
    )

    original_size = size_at(request["photo"]["sizes"], desired_size="Original")

    wikimedia_page_title = api.upload_image(
        filename=request["title"], original_url=original_size["source"], text=wikitext
    )

    wikimedia_page_id = api.add_file_caption(
        filename=request["title"], caption=request["caption"]
    )

    api.add_structured_data(filename=request["title"], data={"claims": request["sdc"]})

    wikimedia_page_title = f"File:{wikimedia_page_title}"

    record_file_created_by_flickypedia(
        flickr_photo_id=request["photo"]["id"],
        wikimedia_page_title=wikimedia_page_title,
        wikimedia_page_id=wikimedia_page_id,
    )

    return {"id": wikimedia_page_id, "title": wikimedia_page_title}
