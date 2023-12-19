import bz2
from collections.abc import Generator
import csv
import re
from typing import Any

import click
import httpx
import mwxml
import tqdm

from flickypedia.backfillr.flickr_matcher import (
    AmbiguousStructuredData,
    find_flickr_photo_id_from_sdc,
    find_flickr_photo_id_from_wikitext,
)
from flickypedia.apis.snapshots import parse_sdc_snapshot
from flickypedia.apis.wikimedia import WikimediaApi


@click.group(
    help="Get information about Flickr photos on WMC",
)
def extractr() -> None:
    pass


@extractr.command(help="Get a list of Flickr photos from SDC.")
@click.argument("SNAPSHOT_PATH")
def get_photos_from_sdc(snapshot_path: str) -> None:
    # The name of the snapshot is something like:
    #
    #     commons-20231009-mediainfo.json.bz2
    #
    # If we can, extract the data and use it to label the spreadsheet we
    # generate
    date_match = re.search(r"\-(\d+)\-", snapshot_path)
    if date_match is None:
        csv_path = "flickr_ids_from_sdc.csv"
    else:
        csv_path = f"flickr_ids_from_sdc.{date_match.group(1)}.csv"

    api = WikimediaApi(client=httpx.Client())

    with open(csv_path, "x") as out_file:
        writer = csv.DictWriter(
            out_file,
            fieldnames=["flickr_photo_id", "wikimedia_page_id", "wikimedia_page_title"],
        )
        writer.writeheader()

        for entry in tqdm.tqdm(parse_sdc_snapshot(snapshot_path)):
            try:
                flickr_photo_id = find_flickr_photo_id_from_sdc(sdc=entry["statements"])
            except AmbiguousStructuredData:
                fresh_sdc = api.get_structured_data(
                    filename=entry["title"].replace("File:", "")
                )

                try:
                    flickr_photo_id = find_flickr_photo_id_from_sdc(sdc=fresh_sdc)
                except AmbiguousStructuredData as exc:
                    print(
                        f'Ambiguity in https://commons.wikimedia.org/?curid={entry["pageid"]}: {exc}'
                    )
                    continue
            except Exception:
                import json

                print(json.dumps(entry["statements"]))
                raise

            if flickr_photo_id is not None:
                writer.writerow(
                    {
                        "flickr_photo_id": flickr_photo_id,
                        "wikimedia_page_id": entry["id"],
                        "wikimedia_page_title": entry["title"],
                    }
                )

    print(csv_path)


def get_files_from_snapshot(snapshot_path: str) -> Generator[Any, None, None]:
    with bz2.open(snapshot_path) as infile:
        dump = mwxml.Dump.from_file(infile)

        for page in tqdm.tqdm(dump):
            if page.namespace != 6:
                continue

            yield page


@extractr.command(help="Get a list of Flickr photos from Wikitext.")
@click.argument("SNAPSHOT_PATH")
def get_photos_from_wikitext(snapshot_path: str) -> None:
    # The name of the snapshot is something like:
    #
    #     commonswiki-20231001-pages-articles-multistream.xml.bz2
    #
    # If we can, extract the data and use it to label the spreadsheet we
    # generate
    date_match = re.search(r"\-(\d+)\-", snapshot_path)
    if date_match is None:
        csv_path = "flickr_ids_from_wikitext.csv"
    else:
        csv_path = f"flickr_ids_from_wikitext.{date_match.group(1)}.csv"

    with open(csv_path, "w") as out_file:
        writer = csv.DictWriter(
            out_file,
            fieldnames=["flickr_photo_id", "flickr_url", "wikimedia_page_id", "wikimedia_page_title"],
        )
        writer.writeheader()

        for page in get_files_from_snapshot(snapshot_path):
            print(page)

            last_revision = [
                rev
                for rev in page
                if rev.text is not None
            ][-1]

            match = find_flickr_photo_id_from_wikitext(last_revision.text)

            print(match)

            break

    #     for entry in tqdm.tqdm(parse_sdc_snapshot(snapshot_path)):
    #         try:
    #             flickr_photo_id = find_flickr_photo_id_from_sdc(sdc=entry["statements"])
    #         except AmbiguousStructuredData:
    #             fresh_sdc = api.get_structured_data(
    #                 filename=entry["title"].replace("File:", "")
    #             )
    #
    #             try:
    #                 flickr_photo_id = find_flickr_photo_id_from_sdc(sdc=fresh_sdc)
    #             except AmbiguousStructuredData as exc:
    #                 print(
    #                     f'Ambiguity in https://commons.wikimedia.org/?curid={entry["pageid"]}: {exc}'
    #                 )
    #                 continue
    #         except Exception:
    #             import json
    #
    #             print(json.dumps(entry["statements"]))
    #             raise
    #
    #         if flickr_photo_id is not None:
    #             writer.writerow(
    #                 {
    #                     "flickr_photo_id": flickr_photo_id,
    #                     "wikimedia_page_id": entry["id"],
    #                     "wikimedia_page_title": entry["title"],
    #                 }
    #             )
    #
    # print(csv_path)
