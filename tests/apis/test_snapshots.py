import pathlib

from flickypedia.apis.snapshots import parse_sdc_snapshot, SnapshotEntry
from flickypedia.utils import validate_typeddict


def test_parse_sdc_snapshot() -> None:
    """
    The snapshot in this test was obtained by slicing a couple of lines
    from the real 20231207 snapshot.
    """
    snapshot_path = pathlib.Path(
        "tests/fixtures/commons-20231207-mediainfo.slice.json.bz2"
    )

    assert len(list(parse_sdc_snapshot(snapshot_path))) == 2


class TestSnapshotEntryType:
    def test_handles_labels(self) -> None:
        entry = {
            "descriptions": {},
            "id": "M369",
            "labels": {"mr": {"language": "mr", "value": "lotus the beauty-full"}},
            "lastrevid": 796923081,
            "modified": "2023-08-29T16:07:16Z",
            "ns": 6,
            "pageid": 369,
            "statements": {"P1163": []},
            "title": "File:Nelumbo nucifera1.jpg",
            "type": "mediainfo",
        }

        validate_typeddict(entry, model=SnapshotEntry)
