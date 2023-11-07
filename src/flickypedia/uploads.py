from typing import Any, List, TypedDict

from celery import current_task, shared_task
from flask_login import current_user
from flickr_photos_api import SinglePhoto

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


@shared_task
def upload_batch_of_photos(
    oauth_info: Any, upload_requests: List[UploadRequest]
) -> Any:
    tracker = ProgressTracker(task_id=current_task.request.id)

    progress_data = [{"req": req, "status": "not_started"} for req in upload_requests]

    tracker.record_progress(data=progress_data)

    for idx, req in enumerate(upload_requests):
        api = current_user.wikimedia_api()

        try:
            # import random
            # import time
            #
            # time.sleep(10)
            #
            # if random.uniform(0, 1) > 0.95:
            #     raise ValueError

            upload_single_image(api, req)
        except Exception as exc:
            progress_data[idx]["status"] = "failed"
            progress_data[idx]["error"] = str(exc)
        else:
            progress_data[idx]["status"] = "succeeded"

        from pprint import pprint

        pprint(progress_data)

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

    wikitext = create_wikitext(license_id=request["photo"]["license"]["id"])

    original_size = size_at(request["photo"]["sizes"], desired_size="Original")

    wikimedia_page_title = api.upload_image(
        filename=request["title"], original_url=original_size["source"], text=wikitext
    )

    wikimedia_page_id = api.add_file_caption(
        filename=request["title"], caption=request["caption"]
    )

    api.add_structured_data(filename=request["title"], data={"claims": request["sdc"]})

    record_file_created_by_flickypedia(
        flickr_photo_id=request["photo"]["id"],
        wikimedia_page_title=f"File:{wikimedia_page_title}",
        wikimedia_page_id=wikimedia_page_id,
    )

    return {"id": wikimedia_page_id, "title": wikimedia_page_title}
