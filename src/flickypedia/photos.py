"""
Some methods for working with collections of photos.
"""

import datetime
from typing import TypedDict

from flask import current_app

from flickypedia.apis.structured_data import create_sdc_claims_for_flickr_photo
from flickypedia.duplicates import find_duplicates, DuplicateInfo
from flickypedia.types.flickr import SinglePhoto, Size
from flickypedia.types.structured_data import NewClaims


def size_at(sizes: list[Size], *, desired_size: str) -> Size:
    """
    Given a list of sizes of Flickr photo, return the info about
    the desired size.
    """
    sizes_by_label = {s["label"]: s for s in sizes}

    # Flickr has a published list of possible sizes here:
    # https://www.flickr.com/services/api/misc.urls.html
    #
    # If the desired size isn't available, that means one of two things:
    #
    #   1.  The owner of this photo has done something to restrict downloads
    #       of their photo beyond a certain size.  But CC-licensed photos
    #       are always available to download, so that's not an issue for us.
    #   2.  This photo is smaller than the size we've asked for, in which
    #       case we fall back to Original as the largest possible size.
    #
    try:
        return sizes_by_label[desired_size]
    except KeyError:
        return sizes_by_label["Original"]


class CategorisedPhotos(TypedDict):
    duplicates: dict[str, DuplicateInfo]
    disallowed_licenses: dict[str, str]
    restricted: set[str]
    available: list[SinglePhoto]


def categorise_photos(all_photos: list[SinglePhoto]) -> CategorisedPhotos:
    """
    Given a list of photos from the Flickr API, split them into
    three lists:

    -   okay to choose ("available")
    -   already on Wikimedia Commons ("duplicates")
    -   using a license not allowed on WMC ("disallowed_license")
    -   with a safety level not allowed on WMC ("restricted")

    """
    duplicates = find_duplicates(flickr_photo_ids=[photo["id"] for photo in all_photos])

    disallowed_licenses = {
        photo["id"]: photo["license"]["label"]
        for photo in all_photos
        # Note: it's possible that a photo with a disallowed license
        # may already be on Wikimedia Commons.
        #
        # We want to avoid putting it in this list so we don't
        # double-count photos.
        if photo["license"]["id"] not in current_app.config["ALLOWED_LICENSES"]
        and photo["id"] not in duplicates
    }

    restricted_photos = {
        photo["id"]
        for photo in all_photos
        if photo["id"] not in duplicates
        and photo["id"] not in disallowed_licenses
        and photo["safety_level"] != "safe"
    }

    available_photos = [
        photo
        for photo in all_photos
        if photo["id"] not in duplicates
        and photo["id"] not in disallowed_licenses
        and photo["id"] not in restricted_photos
    ]

    assert len(duplicates) + len(disallowed_licenses) + len(available_photos) + len(
        restricted_photos
    ) == len(all_photos)

    return {
        "duplicates": duplicates,
        "disallowed_licenses": disallowed_licenses,
        "restricted": restricted_photos,
        "available": available_photos,
    }


class EnrichedPhoto(TypedDict):
    photo: SinglePhoto
    sdc: NewClaims


def enrich_photo(
    photos: list[SinglePhoto], wikimedia_username: str, retrieved_at: datetime.datetime
) -> list[EnrichedPhoto]:
    """
    Create a list of photos which includes their structured data.
    """
    result: list[EnrichedPhoto] = []

    for p in photos:
        result.append(
            {
                "photo": p,
                "sdc": create_sdc_claims_for_flickr_photo(p, retrieved_at=retrieved_at),
            }
        )

    return result
