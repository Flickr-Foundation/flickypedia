"""
Some functions for caching photo data.

The Flickr API doesn't always return stable/consistent results.
In particular, tags and searches can vary slightly from request
to request.  Or a user could add/change their photos while
somebody is using Flickypedia.

To avoid this becoming an issue, we keep a cache of Flickr API
responses.  Whenever a user looks up photos for the first time,
we save the API response in this cache.  We can then retrieve
the cached response later, to give Flickypedia users a consistent
view of Flickr data.
"""

from datetime import datetime, timezone
import json
import os
import uuid

from flask import current_app
from nitrate.json import NitrateDecoder, NitrateEncoder

from flickypedia.types.flickr import GetPhotosData


def get_cached_photos_data(cache_id: str) -> GetPhotosData:
    """
    Retrieve some cached photos data.
    """
    cache_dir = current_app.config["FLICKR_API_RESPONSE_CACHE"]

    with open(os.path.join(cache_dir, cache_id + ".json")) as infile:
        cached_data = json.load(infile, cls=NitrateDecoder)

    return cached_data["value"]  # type: ignore


def save_cached_photos_data(photos_data: GetPhotosData) -> str:
    """
    Cache an API response.

    Returns a cache ID which can be used to retrieve this response later.
    """
    cache_dir = current_app.config["FLICKR_API_RESPONSE_CACHE"]
    response_id = str(uuid.uuid4())

    os.makedirs(cache_dir, exist_ok=True)

    out_data = {
        "saved_at": datetime.now(tz=timezone.utc),
        "value": photos_data,
    }

    with open(os.path.join(cache_dir, response_id + ".json"), "w") as outfile:
        outfile.write(json.dumps(out_data, cls=NitrateEncoder))

    return response_id


def remove_cached_photos_data(cache_id: str) -> None:
    """
    Remove a cached API response.
    """
    cache_dir = current_app.config["FLICKR_API_RESPONSE_CACHE"]

    os.unlink(os.path.join(cache_dir, cache_id + ".json"))
