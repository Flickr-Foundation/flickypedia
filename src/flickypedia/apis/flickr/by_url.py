from datetime import datetime, timezone

from flask import current_app
from flickr_photos_api import FlickrApi
from flickr_url_parser import ParseResult

from flickypedia.types.flickr import GetPhotosData
from .collection_methods import (
    get_photos_in_album,
    get_photos_in_gallery,
    get_photos_in_group_pool,
    get_photos_in_user_photostream,
    get_photos_with_tag,
)


def get_photos_from_flickr(parsed_url: ParseResult) -> GetPhotosData:
    """
    Get a collection of photos from Flickr.
    """
    retrieved_at = datetime.now(tz=timezone.utc)

    api = FlickrApi.with_api_key(
        api_key=current_app.config["FLICKR_API_KEY"],
        user_agent=current_app.config["USER_AGENT"],
    )

    if parsed_url["type"] == "single_photo":
        photo = api.get_single_photo(photo_id=parsed_url["photo_id"])

        return {
            "photos": [photo],
            "owner": photo["owner"],
            "retrieved_at": retrieved_at,
        }

    elif parsed_url["type"] == "album":
        album_resp = get_photos_in_album(
            api,
            user_url=parsed_url["user_url"],
            album_id=parsed_url["album_id"],
            page=parsed_url["page"],
            per_page=100,
        )

        return {**album_resp, "retrieved_at": retrieved_at}

    elif parsed_url["type"] == "user":
        user_resp = get_photos_in_user_photostream(
            api, user_url=parsed_url["user_url"], page=parsed_url["page"], per_page=100
        )

        return {
            **user_resp,
            "owner": user_resp["photos"][0]["owner"],
            "retrieved_at": retrieved_at,
        }
    elif parsed_url["type"] == "gallery":
        gallery_resp = get_photos_in_gallery(
            api,
            gallery_id=parsed_url["gallery_id"],
            page=parsed_url["page"],
            per_page=100,
        )

        return {**gallery_resp, "retrieved_at": retrieved_at}
    elif parsed_url["type"] == "group":
        group_resp = get_photos_in_group_pool(
            api,
            group_url=parsed_url["group_url"],
            page=parsed_url["page"],
            per_page=100,
        )

        return {**group_resp, "retrieved_at": retrieved_at}
    elif parsed_url["type"] == "tag":
        tag_resp = get_photos_with_tag(
            api, tag=parsed_url["tag"], page=parsed_url["page"], per_page=100
        )

        return {**tag_resp, "retrieved_at": retrieved_at}
    else:  # pragma: no cover
        raise TypeError(f"Unrecognised URL type: {parsed_url['type']}")
