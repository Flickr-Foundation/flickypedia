import csv
import re

import click
import tqdm

from flickypedia.apis.snapshots import parse_sdc_snapshot
from .matcher import find_matched_photos


@click.group(help="Get information about Flickr photos on WMC")
def extractr() -> None:
    pass


@extractr.command(help="Get a list of Flickr photos on Commons.")
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

    # Note: this snapshot takes a long time to rebuild, so we open it in mode `x`.
    # This means the CLI will refuse to overwrite an already-created spreadsheet.
    with open(csv_path, "x") as out_file:
        writer = csv.DictWriter(
            out_file,
            fieldnames=["flickr_photo_id", "wikimedia_page_id", "wikimedia_page_title"],
        )
        writer.writeheader()

        entries = tqdm.tqdm(parse_sdc_snapshot(snapshot_path))

        for m in find_matched_photos(entries):  # type: ignore
            writer.writerow(m)

    print(csv_path)
