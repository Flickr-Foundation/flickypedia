import bz2
import csv
import json
import re

import click
import httpx
import tqdm

from flickypedia.backfillr.flickr_matcher import (
    AmbiguousStructuredData,
    find_flickr_photo_id_from_sdc,
)
from flickypedia.apis.structured_data.wikidata import WikidataProperties
from flickypedia.apis.snapshots import parse_sdc_snapshot
from flickypedia.apis.wikimedia import WikimediaApi


@click.group(
    help="Get information about Flickr photos on WMC",
)
def extractr() -> None:
    pass


@extractr.command(help="Get a list of Flickr photos on Commons.")
@click.argument("SNAPSHOT_PATH")
def get_list_of_photos(snapshot_path: str) -> None:
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

    with open(csv_path, "w") as out_file:
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


@extractr.command(help="Create a snapshot with a reduced set of fields.")
@click.argument("SNAPSHOT_PATH")
@click.option("--fields")
def create_reduced_snapshot(snapshot_path: str, fields: str) -> None:
    out_path = snapshot_path.replace(".json.bz2", "." + fields + ".json.bz2").replace(".json.gz", "." + fields + ".json.gz")

    assert out_path != snapshot_path

    matched_fields = set(
        getattr(WikidataProperties, f.strip())
        for f in fields.split(",")
    )

    print(f"Detected property IDs as {matched_fields}")

    with bz2.open(out_path, "x") as out_file:
        for entry in tqdm.tqdm(parse_sdc_snapshot(snapshot_path)):
            entry['statements'] = {k: v for k, v in entry['statements'].items() if k in matched_fields}
            if not entry['statements']:
                continue

            out_file.write(json.dumps(entry).encode("utf8") + b'\n')

    print(out_path)
