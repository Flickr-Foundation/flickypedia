from collections.abc import Iterator
import sys
import typing

from flickypedia.backfillr.flickr_matcher import (
    AmbiguousStructuredData,
    find_flickr_photo_id_from_sdc,
)
from flickypedia.apis.snapshots import SnapshotEntry


class MatchedPhoto(typing.TypedDict):
    flickr_photo_id: str
    wikimedia_page_id: str
    wikimedia_page_title: str


def find_matched_photos(entries: Iterator[SnapshotEntry]) -> Iterator[MatchedPhoto]:
    """
    Given the SDC for an existing set of files on Wikimedia Commons,
    try to find whether there's a matching photo.
    """
    for entry in entries:
        try:
            photo_id = find_flickr_photo_id_from_sdc(sdc=entry["statements"])
            if photo_id is not None:
                yield {
                    "flickr_photo_id": photo_id["photo_id"],
                    "wikimedia_page_id": entry["id"],
                    "wikimedia_page_title": entry["title"],
                }
        except AmbiguousStructuredData as exc:
            print(
                f'Ambiguity in https://commons.wikimedia.org/?curid={entry["pageid"]}: {exc}',
                file=sys.stderr,
            )
        except Exception as exc:
            print(
                f'Unable to find photo ID in https://commons.wikimedia.org/?curid={entry["pageid"]}: {exc}',
                file=sys.stderr,
            )
