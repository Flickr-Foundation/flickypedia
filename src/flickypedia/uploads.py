import datetime

from flickypedia.apis.structured_data import create_sdc_claims_for_flickr_photo
from flickypedia.apis.wikimedia import WikimediaApi
from flickypedia.apis.wikitext import create_wikitext
from flickypedia.types import DateTaken, FlickrUser


def upload_single_image(
    api: WikimediaApi,
    photo_id: str,
    user: FlickrUser,
    filename: str,
    file_caption: str,
    date_taken: DateTaken,
    date_posted: datetime.datetime,
    license_id: str,
    jpeg_url: str,
):
    """
    Upload a photo from Flickr to Wikimedia Commons.

    This includes:

    -   Copying the photo from Flickr to Wikimedia Commons
    -   Adding the file caption supplied by the user
    -   Adding the structured data to the photo

    """
    photo_url = f"https://www.flickr.com/photos/{user['id']}/{photo_id}/"

    wikitext = create_wikitext(
        photo_url=photo_url,
        date_taken=date_taken,
        user=user,
        license_id=license_id,
    )

    structured_data = create_sdc_claims_for_flickr_photo(
        photo_id=photo_id,
        user=user,
        copyright_status="copyrighted",
        jpeg_url=jpeg_url,
        license_id=license_id,
        date_posted=date_posted,
        date_taken=date_taken,
    )

    api.upload_image(filename=filename, jpeg_url=jpeg_url, text=wikitext)

    api.add_file_caption(filename=filename, language="en", value=file_caption)

    api.add_structured_data(filename=filename, data={"claims": structured_data})

    # TODO: Record the fact that we've uploaded this image into
    # Wikimedia Commons, so we don't try to offer it for upload again.
