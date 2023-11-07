from typing import Any, List, TypedDict

from celery import current_task, shared_task
from flask_login import current_user
from flickr_photos_api import SinglePhoto

from flickypedia.apis.structured_data import create_sdc_claims_for_flickr_photo
from flickypedia.apis.wikimedia import ShortCaption, WikimediaApi
from flickypedia.apis.wikitext import create_wikitext
from flickypedia.duplicates import record_file_created_by_flickypedia
from flickypedia.photos import size_at
from flickypedia.tasks import ProgressTracker


@shared_task
def upload_batch_of_photos(oauth_info: Any, photos_to_upload: List[Any]) -> Any:
    tracker = ProgressTracker(task_id=current_task.request.id)

    progress_data = [
        {"photo_id": photo["id"], "status": "not_started"} for photo in photos_to_upload
    ]

    tracker.record_progress(data=progress_data)

    for idx, photo in enumerate(photos_to_upload):
        api = current_user.wikimedia_api()

        try:
            # import random
            # import time
            #
            # time.sleep(10)
            #
            # if random.uniform(0, 1) > 0.95:
            #     raise ValueError
            single_photo: SinglePhoto = {
                "id": photo["id"],
                "url": photo["photo_url"],
                "owner": photo["owner"],
                "license": {"id": photo["license_id"], "label": "?", "url": "?"},
                "sizes": [
                    {
                        "label": "Original",
                        "source": photo["original_url"],
                        "media": "photo",
                        "width": -1,
                        "height": -1,
                    }
                ],
                "title": None,
                "description": None,
                "date_posted": photo["date_posted"],
                "date_taken": photo["date_taken"],
                "safety_level": "safe",
                "original_format": "jpeg",
            }

            upload_single_image(
                api,
                photo=single_photo,
                filename=photo["title"],
                caption=photo["short_caption"],
            )
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


def upload_single_image(
    api: WikimediaApi, photo: SinglePhoto, filename: str, caption: ShortCaption
) -> UploadResult:
    """
    Upload a photo from Flickr to Wikimedia Commons.

    This includes:

    -   Copying the photo from Flickr to Wikimedia Commons
    -   Adding the file caption supplied by the user
    -   Adding the structured data to the photo

    """

    wikitext = create_wikitext(license_id=photo["license"]["id"])

    structured_data = create_sdc_claims_for_flickr_photo(photo=photo)

    original_size = size_at(photo["sizes"], desired_size="Original")

    wikimedia_page_title = api.upload_image(
        filename=filename, original_url=original_size["source"], text=wikitext
    )

    wikimedia_page_id = api.add_file_caption(filename=filename, caption=caption)

    api.add_structured_data(filename=filename, data={"claims": structured_data})

    record_file_created_by_flickypedia(
        flickr_photo_id=photo["id"],
        wikimedia_page_title=f"File:{wikimedia_page_title}",
        wikimedia_page_id=wikimedia_page_id,
    )

    return {"id": wikimedia_page_id, "title": wikimedia_page_title}
