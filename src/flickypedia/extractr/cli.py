import bz2
from collections.abc import Generator
import csv
import glob
import re
import sqlite3
from typing import Any

import click
import httpx
import mwxml
from sqlite_utils import Database
import tqdm

from flickypedia.backfillr.flickr_matcher import (
    AmbiguousStructuredData,
    find_flickr_photo_id_from_sdc,
    find_flickr_photo_id_from_wikitext,
)
from flickypedia.apis.snapshots import parse_sdc_snapshot
from flickypedia.apis.wikimedia import WikimediaApi


def get_database(path: str) -> Database:
    db = Database(path)

    db["flickr_photos_on_wikimedia"].create(
        {
            "flickr_photo_id": str,
            "flickr_photo_url": str,
            "wikimedia_page_id": str,
            "wikimedia_page_title": str,
        },
        pk="flickr_photo_id",
        not_null=["flickr_photo_id", "wikimedia_page_id", "wikimedia_page_title"],
        if_not_exists=True,
    )

    return db


@click.group(
    help="Get information about Flickr photos on WMC",
)
def extractr() -> None:
    pass


def get_page_id(sdc):
    for v in sdc.values():
        for s in v:
            return s["id"].split("$")[0]


@extractr.command(help="Get Flickr photo data from SDC for a single photo.")
@click.argument("TITLE")
def get_single_photo_from_sdc(title) -> None:
    db = get_database("data/duplicates/flickr_ids_from_individual_photos.sqlite")

    api = WikimediaApi(client=httpx.Client())

    assert not title.startswith("File:")
    sdc = api.get_structured_data(filename=title)

    try:
        flickr_photo_id = find_flickr_photo_id_from_sdc(sdc=sdc)
    except AmbiguousStructuredData as exc:
        print(f"Ambiguity in https://commons.wikimedia.org/wiki/File:{title}: {exc}")
        return

    page_id = get_page_id(sdc)

    if flickr_photo_id is not None:
        print(f'{title} ~> {flickr_photo_id["photo_id"]}')
        db["flickr_photos_on_wikimedia"].upsert(
            {
                "flickr_photo_id": flickr_photo_id["photo_id"],
                "flickr_photo_url": flickr_photo_id["url"],
                "wikimedia_page_id": page_id,
                "wikimedia_page_title": title,
            },
            pk="flickr_photo_id",
            not_null=["flickr_photo_id", "wikimedia_page_id", "wikimedia_page_title"],
        )
    else:
        print(f"??? https://commons.wikimedia.org/wiki/File:{title}")


@extractr.command(help="Get a list of Flickr photos from SDC.")
@click.argument("SNAPSHOT_PATH")
def get_photos_from_sdc(snapshot_path: str) -> None:
    # The name of the snapshot is something like:
    #
    #     commons-20231009-mediainfo.json.bz2
    #
    # Extract the data and use it to label the database we generate.
    date_match = re.search(r"\-(\d+)\-", snapshot_path)
    assert date_match is not None

    db_path = f"data/duplicates/flickr_ids_from_sdc.{date_match.group(1)}.sqlite"
    db = get_database(db_path)

    api = WikimediaApi(client=httpx.Client())

    known_page_ids = {
        row["wikimedia_page_id"] for row in db["flickr_photos_on_wikimedia"].rows
    }

    for entry in tqdm.tqdm(parse_sdc_snapshot(snapshot_path)):
        if entry["id"] in known_page_ids:
            continue

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
            # raise

        if flickr_photo_id is not None:
            db["flickr_photos_on_wikimedia"].upsert(
                {
                    "flickr_photo_id": flickr_photo_id["photo_id"],
                    "flickr_photo_url": flickr_photo_id["url"],
                    "wikimedia_page_id": entry["id"],
                    "wikimedia_page_title": entry["title"],
                },
                pk="flickr_photo_id",
                not_null=[
                    "flickr_photo_id",
                    "wikimedia_page_id",
                    "wikimedia_page_title",
                ],
            )

    print(db_path)


def get_files_from_snapshot(snapshot_path: str) -> Generator[Any, None, None]:
    with bz2.open(snapshot_path) as infile:
        dump = mwxml.Dump.from_file(infile)

        for page in tqdm.tqdm(dump):
            if page.namespace != 6:
                continue

            yield page


def get_wikimedia_page_ids():
    for path in glob.glob("data/duplicates/flickr_ids*.sqlite"):
        con = sqlite3.connect(path)
        cur = con.cursor()
        cur.execute("SELECT wikimedia_page_id from flickr_photos_on_wikimedia")

        while True:
            row = cur.fetchone()
            if row is None:
                break
            yield row[0].replace("M", "")


@extractr.command(help="Get a list of Flickr photos from Wikitext.")
@click.argument("SNAPSHOT_PATH")
def get_photos_from_revisions(snapshot_path: str) -> None:
    # The name of the snapshot is something like:
    #
    #     commonswiki-20231001-pages-articles-multistream.xml.bz2
    #
    # Use it to label the database we create.
    date_match = re.search(r"\-(\d+)\-", snapshot_path)
    assert date_match is not None

    db_path = f"data/duplicates/flickr_ids_from_revisions.{date_match.group(1)}.sqlite"
    db = get_database(db_path)

    api = WikimediaApi(client=httpx.Client())

    known_page_ids = set(get_wikimedia_page_ids())

    for page in get_files_from_snapshot(snapshot_path):
        if str(page.id) in known_page_ids:
            continue

        last_revision = [rev for rev in page if rev.text is not None][-1]

        if "flickr.com" not in last_revision.text:
            continue

        # We have to get the Wikitext so it can be rendered as raw HTML
        wikitext = api.get_wikitext(filename=f"File:{page.title}")

        match = find_flickr_photo_id_from_wikitext(wikitext, filename=page.title)

        if match is not None:
            db["flickr_photos_on_wikimedia"].upsert(
                {
                    "flickr_photo_id": match["photo_id"],
                    "flickr_photo_url": match["url"] or "",
                    "wikimedia_page_id": page.id,
                    "wikimedia_page_title": page.title,
                },
                pk="flickr_photo_id",
                not_null=[
                    "flickr_photo_id",
                    "wikimedia_page_id",
                    "wikimedia_page_title",
                ],
            )
        else:
            import subprocess

            subprocess.call(
                ["flickypedia", "extractr", "get-single-photo-from-sdc", page.title]
            )
