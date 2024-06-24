import datetime
import typing

from flickr_photos_api import SinglePhoto

from .statements import (
    create_copyright_status_statement,
    create_date_taken_statement,
    create_flickr_creator_statement,
    create_flickr_photo_id_statement,
    create_license_statement,
    create_location_statement,
    create_published_in_statement,
    create_source_statement,
)
from .types import NewClaims


def _create_sdc_claims_for_flickr_photo(
    photo: SinglePhoto,
    *,
    mode: typing.Literal["new_photo", "existing_photo"],
    retrieved_at: datetime.datetime | None = None,
) -> NewClaims:
    """
    Creates a complete structured data claim for a Flickr photo.

    This is the main entry point into this file for the rest of Flickypedia.
    """
    photo_id_statement = create_flickr_photo_id_statement(photo_id=photo["id"])
    creator_statement = create_flickr_creator_statement(user=photo["owner"])

    statements = [
        photo_id_statement,
        creator_statement,
    ]

    # Note: the "Original" size is not guaranteed to be available
    # for all Flickr photos (in particular those who've disabled
    # downloads).
    #
    # Downloads are always available for CC-licensed or public domain
    # photos, which will be any new uploads, but they may not be available
    # if we're looking at photos whose license have changed since they
    # were initial uploaded to Wikimedia Commons.
    try:
        original_size = [s for s in photo["sizes"] if s["label"] == "Original"][0]
    except IndexError:
        if mode == "new_photo":  # pragma: no cover
            raise

        source_statement = create_source_statement(
            photo_id=photo["id"],
            photo_url=photo["url"],
            original_url=None,
            retrieved_at=None,
        )

        statements.append(source_statement)
    else:
        source_statement = create_source_statement(
            photo_id=photo["id"],
            photo_url=photo["url"],
            original_url=original_size["source"],
            retrieved_at=retrieved_at,
        )

        statements.append(source_statement)

    # We only include the license statement for new uploads -- that field
    # is already pretty well-populated for existing photos, and licenses
    # can have changed since a photo was initially uploaded to Flickr.
    #
    # TODO: Investigate whether we can do anything here with license history.
    if mode == "new_photo":
        license_statement = create_license_statement(license_id=photo["license"]["id"])

        copyright_statement = create_copyright_status_statement(
            license_id=photo["license"]["id"]
        )

        statements.extend([license_statement, copyright_statement])

    location_statement = create_location_statement(location=photo["location"])

    if location_statement is not None:
        statements.append(location_statement)

    if photo["date_taken"] is not None:
        statements.append(create_date_taken_statement(date_taken=photo["date_taken"]))

    published_in_statement = create_published_in_statement(
        date_posted=photo["date_posted"]
    )

    statements.append(published_in_statement)

    return {"claims": statements}


def create_sdc_claims_for_new_flickr_photo(
    photo: SinglePhoto, retrieved_at: datetime.datetime
) -> NewClaims:
    """
    Create the SDC claims for a new upload to Wikimedia Commons.
    """
    return _create_sdc_claims_for_flickr_photo(
        photo, mode="new_photo", retrieved_at=retrieved_at
    )


def create_sdc_claims_for_existing_flickr_photo(photo: SinglePhoto) -> NewClaims:
    """
    Create the SDC claims for a photo which has already been uploaded to WMC.

    This is slightly different to the SDC we create for new uploads:

    *   We don't write a "retrieved at" qualifier, because it would tell
        you when the bot ran rather than when the photo was uploaded to Commons.

    *   We don't include a copyright license/status statement.  Flickr users
        often change their license after it was copied to Commons, and then
        the backfillr bot gets confused because it doesn't know how to map
        the new license, or it doesn't know how to reconcile the conflicting SDC.

    """
    return _create_sdc_claims_for_flickr_photo(photo, mode="existing_photo")
