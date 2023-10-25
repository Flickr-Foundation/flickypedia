"""
This file implements the duplicate detection logic for Flickypedia.

Currently this looks for SQLite databases in the DUPLICATE_DATABASE_DIRECTORY
folder.  These databases should have a table ``flickr_photos_on_wikimedia``
with at least two columns:

    CREATE TABLE flickr_photos_on_wikimedia (
        flickr_photo_id TEXT PRIMARY KEY,
        wikimedia_page_title TEXT NOT NULL,
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
        {}

        >>> find_duplicates(flickr_photo_ids=['9999819294'])
        {"9999819294": {"id": "M29907038", "title": "File:Museu da Ciência (9999819294).jpg"}}

    """
    if not flickr_photo_ids:
        return {}

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

    return result


def create_link_to_commons(duplicates):
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
