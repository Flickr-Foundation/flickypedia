from celery import current_task, shared_task
import datetime

from flickypedia.apis.flickr import DateTaken, FlickrUser
from flickypedia.apis.structured_data import create_sdc_claims_for_flickr_photo
from flickypedia.apis.wikimedia import WikimediaApi
from flickypedia.apis.wikitext import create_wikitext
from flickypedia.duplicates import record_file_created_by_flickypedia
from flickypedia.tasks import ProgressTracker


@shared_task
def upload_batch_of_photos(oauth_info, photos_to_upload):
    tracker = ProgressTracker(task_id=current_task.request.id)

    tracker.record_progress(
        data=[
            {"photo_id": photo["id"], "status": "not_started"}
            for photo in photos_to_upload
        ]
    )

    for idx, photo in enumerate(photos_to_upload):
        wikitext = create_wikitext(license_id=photo["license_id"])

        print(wikitext)


def upload_single_image(
    api: WikimediaApi,
    photo_id: str,
    photo_url: str,
    user: FlickrUser,
    filename: str,
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

    wikipedia_page_title = api.upload_image(
        filename=filename, original_url=original_url, text=wikitext
    )

    wikipedia_page_id = api.add_file_caption(
        filename=filename, language="en", value=file_caption
    )

    api.add_structured_data(filename=filename, data={"claims": structured_data})

    record_file_created_by_flickypedia(
        flickr_photo_id=photo_id,
        wikimedia_page_title=f"File:{wikipedia_page_title}",
        wikimedia_page_id=wikipedia_page_id,
    )

    # TODO: Record the fact that we've uploaded this image into
    # Wikimedia Commons, so we don't try to offer it for upload again.
