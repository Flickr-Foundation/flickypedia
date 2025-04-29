from flickr_api import FlickrApi

from flickypedia.types.flickr import FlickrPhoto


def get_single_photo(api: FlickrApi, photo_id: str) -> FlickrPhoto:
    """
    Look up a single photo in the Flickr API.
    """
    photo = api.get_single_photo(photo_id=photo_id)

    return {
        "id": photo["id"],
        "title": photo["title"],
        "description": photo["description"],
        "owner": photo["owner"],
        "date_taken": photo["date_taken"],
        "date_posted": photo["date_posted"],
        "location": photo["location"],
        "license": photo["license"],
        "sizes": photo["sizes"],
        "tags": photo["tags"],
        "machine_tags": photo["machine_tags"],
        "safety_level": photo["safety_level"],
        "url": photo["url"],
        "original_format": photo["original_format"],
    }
