"""
Code for dealing with the snapshots of Wikimedia Commons data,
as downloaded from https://dumps.wikimedia.org/other/wikibase/commonswiki/
"""

import bz2
from collections.abc import Iterator
import json
from pprint import pprint
import typing

from pydantic import ValidationError

from flickypedia.types import Path, validate_typeddict
from flickypedia.types.structured_data import ExistingClaims


class MonolingualValue(typing.TypedDict):
    language: str
    value: str


SnapshotEntry = typing.TypedDict(
    "SnapshotEntry",
    {
        "id": str,
        "pageid": int,
        "type": typing.Literal["mediainfo"],
        "ns": typing.Literal[6],
        "title": "str",
        "lastrevid": int,
        "modified": "str",
        "statements": ExistingClaims,
        "labels": dict[str, MonolingualValue],
        "descriptions": dict[str, MonolingualValue],
    },
)


def parse_sdc_snapshot(path: Path) -> Iterator[SnapshotEntry]:
    """
    Given a snapshot of SDC from Wikimedia Commons, generate every entry.
    """
    # The file is returned as a massive JSON object, but we can
    # stream it fairly easily: there's an opening [, then one
    # object per line, i.e.:
    #
    #     [
    #       {…},
    #       {…},
    #       {…}
    #     ]
    #
    # So if we go line-by-line, we can stream the file without having
    # to load it all into memory.
    with bz2.open(path) as in_file:
        for line in in_file:
            if line.strip() in {b"[", b"]"}:
                continue

            data = json.loads(line.replace(b",\n", b""))

            try:
                yield validate_typeddict(data, model=SnapshotEntry)

            # This doesn't happen with current snapshots (20231124) so
            # it suggests our model is pretty complete, but we leave
            # this here as a defensive measure in case the snapshot
            # format changes at some point.
            except ValidationError:
                pprint(data)
                raise
