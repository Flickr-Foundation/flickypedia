"""
This file implements the duplicate detection logic for Flickypedia.

Currently this looks for SQLite databases in the DUPLICATE_DATABASE_DIRECTORY
folder.  These databases should have a table ``flickr_photos_on_wikimedia``
with at least two columns:

    CREATE TABLE flickr_photos_on_wikimedia (
        flickr_photo_id TEXT PRIMARY KEY,
        wikimedia_page_id TEXT NOT NULL
    )

This database can be created from a WMC snapshot by scripts in this repo
(see the ``duplicates_from_sdc`` folder), and at some point we might use
the Wikimedia Commons Query Service instead -- but for now this is
our approach.

"""

import os
import sqlite3

from flask import current_app


def find_duplicates(flickr_photo_ids):
    """
    Given a list of Flickr photo IDs, return the duplicates files found
    on Wikimedia Commons.

    The result with be a dictionary in which duplicate photo IDs are keys,
    and the values are the name of the file on Wikimedia Commons.

        >>> find_duplicates(flickr_photo_ids=['12345678901234567890'])
        []

        >>> find_duplicates(flickr_photo_ids=['53240661807'])
        [("53240661807", "M138598125")]

    The result is a list of tuples, to match the order of the original
    Flickr IDs.

    """
    if not flickr_photo_ids:
        return []

    duplicate_dir = current_app.config["DUPLICATE_DATABASE_DIRECTORY"]

    result = {}

    for name in os.listdir(duplicate_dir):
        if name.endswith(".sqlite"):
            con = sqlite3.connect(
                f"file:{os.path.join(duplicate_dir, name)}?mode=ro", uri=True
            )
            cur = con.cursor()

            query = ",".join(flickr_photo_ids)

            cur.execute(
                f"""
                SELECT flickr_photo_id,wikimedia_page_id
                FROM flickr_photos_on_wikimedia
                WHERE flickr_photo_id IN ({query});
                """
            )

            for row in cur.fetchall():
                assert row[0] in flickr_photo_ids
                result[row[0]] = row[1]

    return [
        (photo_id, result[photo_id])
        for photo_id in flickr_photo_ids
        if photo_id in result
    ]


def create_media_search_link(duplicates):
    """
    Given a collection of duplicates from ``find_duplicates``, create
    a link to find those images on Wikimedia Commons.
    """
    page_ids = [dupe.replace("M", "") for _, dupe in duplicates]

    return f"https://commons.wikimedia.org/wiki/Special:MediaSearch?type=image&search=pageid:{'|'.join(page_ids)}"
