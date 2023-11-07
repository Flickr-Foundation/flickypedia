import datetime

from celery import current_task, shared_task
from flickr_photos_api import DateTaken, User as FlickrUser

from flickypedia.apis.structured_data import create_sdc_claims_for_flickr_photo
from flickypedia.apis.wikimedia import WikimediaApi
from flickypedia.apis.wikitext import create_wikitext
from flickypedia.auth import get_wikimedia_api
from flickypedia.duplicates import record_file_created_by_flickypedia
from flickypedia.tasks import ProgressTracker


@shared_task
def upload_batch_of_photos(oauth_info, photos_to_upload):
    tracker = ProgressTracker(task_id=current_task.request.id)

    progress_data = [
        {"photo_id": photo["id"], "status": "not_started"} for photo in photos_to_upload
    ]

    tracker.record_progress(data=progress_data)

    for idx, photo in enumerate(photos_to_upload):
        api = get_wikimedia_api()

        try:
            # import random
            # import time
            #
            # time.sleep(10)
            #
            # if random.uniform(0, 1) > 0.95:
            #     raise ValueError
            upload_single_image(
                api,
                photo_id=photo["id"],
                photo_url=photo["photo_url"],
                user=photo["owner"],
                filename=photo["title"],
                file_caption_language=photo["short_caption"]["language"],
                file_caption=photo["short_caption"]["text"],
                date_taken=photo["date_taken"],
                date_posted=photo["date_posted"],
                license_id=photo["license_id"],
                original_url=photo["original_url"],
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


def upload_single_image(
    api: WikimediaApi,
    photo_id: str,
    photo_url: str,
    user: FlickrUser,
    filename: str,
    file_caption_language: str,
    file_caption: str,
    date_taken: DateTaken,
    date_posted: datetime.datetime,
    license_id: str,
    original_url: str,
):
    """
    Upload a photo from Flickr to Wikimedia Commons.

    This includes:

    -   Copying the photo from Flickr to Wikimedia Commons
    -   Adding the file caption supplied by the user
    -   Adding the structured data to the photo

    """
    wikitext = create_wikitext(license_id=license_id)

    structured_data = create_sdc_claims_for_flickr_photo(
        photo_id=photo_id,
        photo_url=photo_url,
        user=user,
        copyright_status="copyrighted",
        original_url=original_url,
        license_id=license_id,
        date_posted=date_posted,
        date_taken=date_taken,
    )

    wikimedia_page_title = api.upload_image(
        filename=filename, original_url=original_url, text=wikitext
    )

    wikimedia_page_id = api.add_file_caption(
        filename=filename, language=file_caption_language, value=file_caption
    )

    api.add_structured_data(filename=filename, data={"claims": structured_data})

    record_file_created_by_flickypedia(
        flickr_photo_id=photo_id,
        wikimedia_page_title=f"File:{wikimedia_page_title}",
        wikimedia_page_id=wikimedia_page_id,
    )

    return {"id": wikimedia_page_id, "title": wikimedia_page_title}
