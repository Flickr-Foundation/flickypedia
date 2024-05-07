import csv
import json
import os
import sys

from authlib.integrations.httpx_client import OAuth2Client
import click
from flickr_photos_api import FlickrApi, ResourceNotFound
import httpx
import keyring
import termcolor

from flickypedia.apis.wikimedia import get_filename_from_url, WikimediaApi
from flickypedia.apis.structured_data import create_flickr_photo_id_statement, create_sdc_claims_for_existing_flickr_photo
from flickypedia.types.structured_data import ExistingClaims
from .actions import create_actions
from .flickr_matcher import (
    find_flickr_photo_id_from_sdc,
    find_flickr_photo_id_from_wikitext,
    FindResult,
)


class Backfillr:
    def __init__(self, *, flickr_api: FlickrApi, wikimedia_api: WikimediaApi):
        self.flickr_api = flickr_api
        self.wikimedia_api = wikimedia_api

    def find_flickr_photo(
        self,
        *,
        existing_sdc: ExistingClaims,
        filename: str,
    ) -> FindResult | None:
        find_result = find_flickr_photo_id_from_sdc(existing_sdc)

        if find_result is not None:
            return find_result

        wikitext = self.wikimedia_api.get_wikitext(filename)

        find_result = find_flickr_photo_id_from_wikitext(
            wikitext, filename=f"File:{filename}"
        )

        return find_result

    def update_file(self, *, filename: str) -> None:
        existing_sdc = self.wikimedia_api.get_structured_data(filename=filename)
        flickr_id = self.find_flickr_photo(existing_sdc=existing_sdc, filename=filename)

        if flickr_id is None:
            print(f"Unable to find Flickr ID for {filename}", file=sys.stderr)
            return

        try:
            single_photo = self.flickr_api.get_single_photo(photo_id=flickr_id["photo_id"])
            new_sdc = create_sdc_claims_for_existing_flickr_photo(single_photo)
        except ResourceNotFound:
            new_sdc = {
                'claims': [
                    create_flickr_photo_id_statement(photo_id=flickr_id["photo_id"])
                ]
            }

        actions = create_actions(existing_sdc, new_sdc)

        claims = []
        affected_properties = []

        for a in actions:
            if a["action"] == "unknown":
                print(a["property_id"], "\t", termcolor.colored(a["action"], "red"))
                with open("unknown.json", "a") as outfile:
                    outfile.write(json.dumps({"filename": filename, "property_id": a["property_id"]}) + "\n")
            else:
                print(a["property_id"], "\t", a["action"])

            if a["action"] == "add_missing":
                affected_properties.append(a["property_id"])
                claims.append(a["statement"])
            elif a["action"] == "add_qualifiers":
                claims.append({"id": a["statement_id"], **a["statement"]})
                affected_properties.append(a["property_id"])
            elif a["action"] == "replace_statement":
                claims.append({"id": a["statement_id"], **a["statement"]})
                affected_properties.append(a["property_id"])

        if claims:
            self.wikimedia_api.add_structured_data(
                filename=filename,
                data={"claims": claims},
                summary="Update the [[Commons:Structured data|structured data]] based on metadata from Flickr",
            )
        else:
            print(f"No updates required for {filename}")


@click.group(
    short_help="Improve SDC for existing Flickr photos",
    help="Improve the structured data for Flickr photos which have already been uploaded to Wikimedia Commons.",
)
def backfillr() -> None:
    pass


@backfillr.command(help="Fix the SDC for a single file.")
@click.argument("URL")
def update_single_file(url: str) -> None:
    try:
        filename = get_filename_from_url(url)
    except ValueError:
        raise click.UsageError(
            f"Expected a URL like https://commons.wikimedia.org/wiki/File:<filename>, got {url!r}"
        )

    flickr_api = FlickrApi(
        api_key=keyring.get_password("flickr_api", "key"),
        user_agent="Alex Chan's personal scripts <alex@alexwlchan.net>",
    )

    backfillr = Backfillr(
        flickr_api=flickr_api,
        wikimedia_api=WikimediaApi(
            client=httpx.Client(
                cookies=json.loads(keyring.get_password("flickypedia", "cookies"))
            )
        ),
    )

    backfillr.update_file(filename=filename)


@backfillr.command(help="Fix the SDC for multiple files")
@click.argument("FLICKR_ID_SPREADSHEET")
@click.argument("N")
def update_multiple_files(flickr_id_spreadsheet: str, n: int) -> None:
    flickr_api = FlickrApi(
        api_key=keyring.get_password("flickr_api", "key"),
        user_agent="Alex Chan's personal scripts <alex@alexwlchan.net>",
    )

    backfillr = Backfillr(
        flickr_api=flickr_api,
        wikimedia_api=WikimediaApi(
            client=httpx.Client(
                cookies=json.loads(keyring.get_password("flickypedia", "cookies"))
            )
        ),
    )

    try:
        seen_filenames = set(line.strip() for line in open('seen_filenames.txt'))
    except FileNotFoundError:
        seen_filenames = set()

    updates = 0

    with open(flickr_id_spreadsheet) as in_file:
        for row in csv.DictReader(in_file):
            filename = row['wikimedia_page_title'].replace('File:', '')

            if filename in seen_filenames:
                continue

            print(filename)
            backfillr.update_file(filename=filename)
            print("")

            with open('seen_filenames.txt', 'a') as of:
                updates += 1
                of.write(filename + '\n')

            if updates >= int(n):
                print(f"Completed {updates} updates, exiting")
                break
