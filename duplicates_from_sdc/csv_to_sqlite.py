#!/usr/bin/env python3
"""
Given a spreadsheet of the form:

    flickr_photo_id,wikimedia_title,wikimedia_page_id
    3176098,File:Crocodile grin-scubadive67.jpg,M63606
    7267164,File:Rfid implant after.jpg,M87190
    9494179,File:Madrid Metro Sign.jpg,M137548

which tells you about the Flickr photo IDs in the structured data,
create a SQLite database that will allow fast lookup of photo IDs.

Note: this database will only record the first duplicate of a Flickr photo
on WMC -- the spreadsheet may know about multiple copies, but we only
want the first one.

"""

import csv
import re
import sqlite3
import sys

import tqdm


def unique_rows(csv_path):
    """
    Get the rows from the CSV and de-duplicate by Flickr photo ID.
    """
    stored_ids = set()

    with open(csv_path) as in_file:
        reader = csv.DictReader(in_file)

        for row in tqdm.tqdm(reader):
            if row["flickr_photo_id"] in stored_ids:
                continue

            stored_ids.add(row["flickr_photo_id"])
            yield (
                row["flickr_photo_id"],
                row["wikimedia_title"],
                row["wikimedia_page_id"],
            )


if __name__ == "__main__":
    try:
        csv_path = sys.argv[1]
    except IndexError:
        sys.exit(f"Usage: {__file__} <CSV_PATH>")

    # The name of the CSV is something like:
    #
    #     flickr_ids_from_sdc.20231009.csv
    #
    # If we can, extract the data and use it to label the database we
    # generate
    date_match = re.search(r"\.(\d+)\.", csv_path)
    if date_match is None:
        db_path = "flickr_ids_from_sdc.sqlite"
    else:
        db_path = f"flickr_ids_from_sdc.{date_match.group(1)}.sqlite"

    # Create the database table.
    #
    # The goal is to create fast lookups of Flickr ID -> Wikimedia page,
    # so we make that the primary key.
    con = sqlite3.connect(db_path)

    cur = con.cursor()

    cur.execute(
        """
    CREATE TABLE flickr_photos_on_wikimedia (
        flickr_photo_id TEXT PRIMARY KEY,
        wikimedia_page_title TEXT NOT NULL,
        wikimedia_page_id TEXT NOT NULL
    );
    """
    )

    # Get the rows from the CSV and insert them into the database.
    cur.executemany(
        """
    INSERT INTO flickr_photos_on_wikimedia
    VALUES(?, ?, ?)
    """,
        unique_rows(csv_path),
    )

    con.commit()

    print(db_path)
