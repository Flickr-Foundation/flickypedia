"""
This file implements the duplicate detection logic for Flickypedia.

This tool looks at SQLite databases in DUPLICATE_DATABASE_DIRECTORY.
These databases should have a table ``flickr_photos_on_wikimedia`` like:

    CREATE TABLE flickr_photos_on_wikimedia (
        flickr_photo_id TEXT PRIMARY KEY,
        wikimedia_page_title TEXT NOT NULL,
        wikimedia_page_id TEXT NOT NULL
    )

These databases can come from two places:

*   The Wikimedia Commons snapshot.  We create a database from the snapshot
    using scripts elsewhere in this repo (see ``duplicates_from_sdc``).

    These snapshots are updated weekly by WMC at best, so they may be
    a bit behind the latest uploads.

*   Flickypedia itself.  Whenever it uploads a file, it makes a note of it
    in a dedicated database.  This acts as a ledger of Flickypedia activity
    and prevents double-uploads by the tool.

"""

import os
import sqlite3
from typing import Dict, List, TypedDict

from flask import current_app


class DuplicateInfo(TypedDict):
    id: str
    title: str


def find_duplicates(flickr_photo_ids: List[str]) -> Dict[str, DuplicateInfo]:
    """
    Given a list of Flickr photo IDs, return the duplicates files found
    on Wikimedia Commons.

    The result with be a dictionary in which duplicate photo IDs are keys,
    and the values are the name of the file on Wikimedia Commons.

        >>> find_duplicates(flickr_photo_ids=['12345678901234567890'])
        {}

        >>> find_duplicates(flickr_photo_ids=['9999819294'])
        {"9999819294": {"id": "M29907038", "title": "File:Museu da Ciência (9999819294).jpg"}}

    """
    if not flickr_photo_ids:
        return {}

    duplicate_dir = current_app.config["DUPLICATE_DATABASE_DIRECTORY"]

    result: Dict[str, DuplicateInfo] = {}

    for name in os.listdir(duplicate_dir):
        if name.endswith((".db", ".sqlite")):
            con = sqlite3.connect(
                f"file:{os.path.join(duplicate_dir, name)}?mode=ro", uri=True
            )
            cur = con.cursor()

            query = ",".join(flickr_photo_ids)

            cur.execute(
                f"""
                SELECT flickr_photo_id,wikimedia_page_title,wikimedia_page_id
                FROM flickr_photos_on_wikimedia
                WHERE flickr_photo_id IN ({query});
                """
            )

            titles = [d[0] for d in cur.description]

            for row in cur.fetchall():
                row = dict(zip(titles, row))

                assert row["flickr_photo_id"] in flickr_photo_ids
                result[row["flickr_photo_id"]] = {
                    "title": row["wikimedia_page_title"],
                    "id": row["wikimedia_page_id"],
                }
        elif name != ".DS_Store":  # pragma: no cover
            print(f"Ignoring file {name} which doesn't look like a SQLite database")

    return result


def create_link_to_commons(duplicates: Dict[str, DuplicateInfo]) -> str:
    """
    Given a collection of duplicates from ``find_duplicates``, create
    a link to find those images on Wikimedia Commons.

    If it's a single file, we link directly to the file.
    If it's multiple files, we link to a gallery in MediaSearch.

    """
    assert len(duplicates) > 0

    if len(duplicates) == 1:
        title = list(duplicates.values())[0]["title"]

        return f"https://commons.wikimedia.org/wiki/{title}"
    else:
        # Note: it's fine to sort here, because MediaSearch doesn't
        # seem to care about order.
        #
        # Compare:
        # https://commons.wikimedia.org/wiki/Special:MediaSearch?type=image&search=pageid%3A29907038%7C29907062
        # https://commons.wikimedia.org/wiki/Special:MediaSearch?type=image&search=pageid%3A29907062%7C29907038
        #
        # It'd be nice if we could preserve the order of the original
        # Flickr collection, but there doesn't seem to be a good way
        # to do that.
        page_ids = sorted([dupe["id"].replace("M", "") for dupe in duplicates.values()])

        return f"https://commons.wikimedia.org/wiki/Special:MediaSearch?type=image&search=pageid:{'|'.join(page_ids)}"


def record_file_created_by_flickypedia(
    flickr_photo_id: str, wikimedia_page_title: str, wikimedia_page_id: str
) -> None:
    """
    Create a database entry to mark a file as having been uploaded to
    Wikimedia Commons.

    This will prevent a user accidentally uploading the same file twice
    in quick succession.
    """
    assert wikimedia_page_title.startswith("File:")

    duplicate_dir = current_app.config["DUPLICATE_DATABASE_DIRECTORY"]

    con = sqlite3.connect(os.path.join(duplicate_dir, "flickypedia_uploads.db"))
    cur = con.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS flickr_photos_on_wikimedia (
            flickr_photo_id TEXT PRIMARY KEY,
            wikimedia_page_title TEXT NOT NULL,
            wikimedia_page_id TEXT NOT NULL
        )
        """
    )

    cur.execute(
        "INSERT INTO flickr_photos_on_wikimedia VALUES(?, ?, ?)",
        (flickr_photo_id, wikimedia_page_title, wikimedia_page_id),
    )

    con.commit()
