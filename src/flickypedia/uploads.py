import random
import time

import celery
from celery import shared_task
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    IntegerField,
    DateTimeField,
    StringField,
    SubmitField,
    SelectField,
)
from wtforms.validators import DataRequired

from flickypedia.tasks import ProgressTracker
from flickypedia.apis.wikitext import create_wikitext
from flickypedia.apis.structured_data import create_sdc_claims_for_flickr_photo


class UploadPhotoForm(FlaskForm):
    photo_url = StringField("photo_url", validators=[DataRequired()])
    photo_id = StringField("photo_id", validators=[DataRequired()])
    user_id = StringField("user_id", validators=[DataRequired()])
    username = StringField("username", validators=[DataRequired()])
    realname = StringField("realname", validators=[DataRequired()])

    jpeg_url = StringField("jpeg_url", validators=[DataRequired()])
    license_id = SelectField(
        choices=[("cc-by-2.0", "CC-BY"), ("cc-by-sa-2.0", "CC-BY-SA")]
    )

    filename = StringField("filename", validators=[DataRequired()])
    short_caption = StringField("short_caption", validators=[DataRequired()])

    posted_date = DateTimeField("posted_date", validators=[DataRequired()])
    date_taken = DateTimeField("date_taken", validators=[DataRequired()])
    taken_unknown = BooleanField("taken_unknown", validators=[DataRequired()])
    taken_granularity = IntegerField("taken_granularity", validators=[DataRequired()])

    submit = SubmitField("Upload")


@shared_task(ignore_result=False)
def upload_batch_of_photos(oauth_info, photos_to_upload):
    tracker = ProgressTracker(task_id=celery.current_task.request.id)

    tracker.record_progress(
        data=[
            {"photo_id": photo["photo_id"], "status": "not_started"}
            for photo in photos_to_upload
        ]
    )

    for i, photo in enumerate(photos_to_upload):
        wikitext = create_wikitext(
            photo_url=photo["photo_url"],
            date_taken=photo["date_taken"],
            flickr_user=photo["flickr_user"],
            license_id=photo["license_id"],
        )

        structured_data = create_sdc_claims_for_flickr_photo(
            photo_id=photo["photo_id"],
            user=photo["flickr_user"],
            copyright_status="copyrighted",
            jpeg_url=photo["jpeg_url"],
            license_id=photo["license_id"],
            posted_date=photo["posted_date"],
            date_taken=photo["date_taken"],
        )

        print(wikitext)

        from pprint import pprint

        pprint(structured_data)

        time.sleep(random.uniform(1, 5))

        result = "success" if random.uniform(0, 1) > 0.15 else "failure"

        data = tracker.get_progress()
        data[i]["status"] = result

        tracker.record_progress(data=data)

    return tracker.get_progress()
