import datetime
import sys

import click
import httpx
import keyring

from flickypedia.apis.flickr import FlickrPhotosApi
from flickypedia.apis.structured_data import (
    create_sdc_claims_for_flickr_photo,
    find_flickr_photo_id,
)
from flickypedia.apis.wikimedia import WikimediaApi
from .actions import create_actions


@click.group(
    short_help="Improve SDC for existing Flickr photos",
    help="Improve the structured data for Flickr photos on Commons.",
)
def backfillr() -> None:
    pass


@backfillr.command(help="Fix the SDC for a single file.")
@click.argument("URL")
def update_single_file(url: str) -> None:
    if not url.startswith("https://commons.wikimedia.org/wiki/File:"):
        raise click.UsageError(
            f"Expected a URL like https://commons.wikimedia.org/wiki/File:<filename>, got {url!r}"
        )

    filename = url.replace("https://commons.wikimedia.org/wiki/File:", "")

    wikimedia_api = WikimediaApi(client=httpx.Client())

    existing_sdc = wikimedia_api.get_structured_data(filename=filename)

    photo_id = find_flickr_photo_id(existing_sdc)

    if photo_id is None:
        print("Could not find a Flickr photo ID in the existing SDC!")
        sys.exit(0)

    print(f"Found the Flickr photo ID {photo_id}")

    flickr_api = FlickrPhotosApi(
        api_key=keyring.get_password("flickr_api", "key"),
        user_agent="Flickypedia Backfillr <hello@flickr.org>",
    )

    photo = flickr_api.get_single_photo(photo_id=photo_id)

    new_sdc = create_sdc_claims_for_flickr_photo(
        photo, retrieved_at=datetime.datetime.now()
    )

    actions = create_actions(existing_sdc, new_sdc)

    from pprint import pprint

    pprint(actions)
