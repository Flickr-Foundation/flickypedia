"""
Code for dealing with the snapshots of Wikimedia Commons data,
as downloaded from https://dumps.wikimedia.org/other/wikibase/commonswiki/
"""

import bz2
from collections.abc import Generator
import json
from pprint import pprint
from typing import Literal, TypedDict

from pydantic import ValidationError

from flickypedia.types import Path, validate_typeddict
from flickypedia.types.structured_data import ExistingClaims


class Label(TypedDict):
    language: str
    value: str


SnapshotEntry = TypedDict(
    "SnapshotEntry",
    {
        "id": str,
        "pageid": int,
        "type": Literal["mediainfo"],
        "ns": Literal[6],
        "title": "str",
        "lastrevid": int,
        "modified": "str",
        "statements": ExistingClaims,
        "labels": dict[str, Label],
        "descriptions": dict[str, str],
    },
)


def parse_sdc_snapshot(path: Path) -> Generator[SnapshotEntry, None, None]:
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

            # I've never actually seen what these look like, so I'm not
            # sure I'm modelling them correctly -- so if/when I get
            # an example, log it for inspection.
            if data["descriptions"]:
                pprint(data["descriptions"])

            try:
                yield validate_typeddict(data, model=SnapshotEntry)
            except ValidationError:
                pprint(data)
                raise
