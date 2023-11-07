import json
from typing import List, Literal, TypedDict

from authlib.integrations.httpx_client.oauth2_client import OAuth2Client
from authlib.oauth2.rfc6749.wrappers import OAuth2Token
from celery import current_task, shared_task
from flask import current_app
from flickr_photos_api import SinglePhoto

from flickypedia.apis.structured_data import Statement
from flickypedia.apis.wikimedia import WikimediaApi
from flickypedia.apis.wikitext import create_wikitext
from flickypedia.auth import WikimediaUserSession, user_db
from flickypedia.duplicates import record_file_created_by_flickypedia
from flickypedia.tasks import ProgressTracker
from flickypedia.utils import encrypt_string, size_at


class ShortCaption(TypedDict):
    language: str
    text: str


class PhotoToUpload(TypedDict):
    photo: SinglePhoto
    sdc_statements: List[Statement]
    title: str
    short_caption: ShortCaption


class ProgressData(TypedDict):
    data: PhotoToUpload
    status: Literal['not_started', 'failed', 'succeeded']


@shared_task
def upload_batch_of_photos(userid: str, token, key, photos_to_upload: List[PhotoToUpload]):
    tracker = ProgressTracker(task_id=current_task.request.id)

    progress_data: List[ProgressData] = [
        {
            'data': data,
            'status': 'not_started'
        }
        for data in photos_to_upload
    ]

    config = current_app.config["OAUTH2_PROVIDERS"]["wikimedia"]

    def update_token(token: OAuth2Token, refresh_token: str) -> None:
        this_user = user_db.session.query(WikimediaUserSession).filter(
            WikimediaUserSession.id == userid
        )

        # The user has logged out of the app -- we should keep working
        # on their behalf, but we don't need to save the new
        # token anywhere.
        if this_user is None:
            return

        this_user.encrypted_token = encrypt_string(key=key, plaintext=json.dumps(token))
        user_db.session.commit()

    client = OAuth2Client(
        client_id=config["client_id"],
        client_secret=config["client_secret"],
        token_endpoint=config["token_url"],
        token=token,
        update_token=update_token,
        headers={"User-Agent": current_app.config["USER_AGENT"]},
    )

    wikimedia_api = WikimediaApi(client=client)

    tracker.record_progress(data=progress_data)

    for idx, photo in enumerate(photos_to_upload):
        try:
            import random
            import time

            time.sleep(10)

            if random.uniform(0, 1) > 0.95:
                raise ValueError
            # upload_single_image(
            #     api,
            #     photo_id=photo["id"],
            #     photo_url=photo["photo_url"],
            #     user=photo["owner"],
            #     filename=photo["title"],
            #     file_caption_language=photo["short_caption"]["language"],
            #     file_caption=photo["short_caption"]["text"],
            #     date_taken=photo["date_taken"],
            #     date_posted=photo["date_posted"],
            #     license_id=photo["license_id"],
            #     original_url=photo["original_url"],
            # )
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
    api: WikimediaApi,
    photo_to_upload: PhotoToUpload
) -> UploadResult:
    """
    Upload a photo from Flickr to Wikimedia Commons.

    This includes:

    -   Copying the photo from Flickr to Wikimedia Commons
    -   Adding the file caption supplied by the user
    -   Adding the structured data to the photo

    """
    filename = photo_to_upload['title']
    photo = photo_to_upload['photo']

    wikitext = create_wikitext(license_id=photo['license']['id'])

    wikimedia_page_title = api.upload_image(
        filename=filename,
        original_url=size_at(photo['sizes'], desired_size='Original')['source'],
        text=wikitext
    )

    wikimedia_page_id = api.add_file_caption(
        filename=filename,
        language=photo_to_upload['short_caption']['language'], value=photo_to_upload['short_caption']['text']
    )

    api.add_structured_data(filename=filename, data={"claims": photo_to_upload['sdc_statements']})

    record_file_created_by_flickypedia(
        flickr_photo_id=photo['id'],
        wikimedia_page_title=f"File:{wikimedia_page_title}",
        wikimedia_page_id=wikimedia_page_id,
    )

    return {"id": wikimedia_page_id, "title": wikimedia_page_title}
