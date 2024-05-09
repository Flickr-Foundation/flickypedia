import bz2
import pathlib

from nitrate.types import validate_type
from pydantic import ValidationError
import pytest

from flickypedia.apis.snapshots import parse_sdc_snapshot, SnapshotEntry


def test_parse_sdc_snapshot() -> None:
    """
    The snapshot in this test was obtained by slicing a couple of lines
    from the real 20231207 snapshot.
    """
    snapshot_path = pathlib.Path(
        "tests/fixtures/commons-20231207-mediainfo.slice.json.bz2"
    )

    assert len(list(parse_sdc_snapshot(snapshot_path))) == 2


def test_parse_busted_sdc_snapshot_is_error(tmp_path: pathlib.Path) -> None:
    """
    If there's a line which doesn't match our ``SnapshotEntry`` type,
    we throw an error rather than continuing.
    """
    snapshot_path = tmp_path / "snapshot.json.bz2"

    with bz2.open(snapshot_path, "xb") as out_file:
        out_file.write("""[\n{"data in": "the wrong format"}\n]""".encode("utf8"))

    with pytest.raises(ValidationError):
        list(parse_sdc_snapshot(snapshot_path))


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

        validate_type(entry, model=SnapshotEntry)

    def test_handles_descriptions(self) -> None:
        entry = {
            "descriptions": {
                "de": {
                    "language": "de",
                    "value": "Marienkapelle neben Haus Visbeck in der Bauerschaft Dernekamp, Kirchspiel, Dülmen, Nordrhein-Westfalen, Deutschland",
                },
                "en": {
                    "language": "en",
                    "value": "St Mary’s Chapel next to Visbeck manor in the Dernekamp hamlet, Kirchspiel, Dülmen, North Rhine-Westphalia, Germany",
                },
            },
            "id": "M25872413",
            "labels": {},
            "lastrevid": 795294648,
            "modified": "2023-08-23T09:59:31Z",
            "ns": 6,
            "pageid": 25872413,
            "statements": {},
            "title": "File:Kirchspiel (Dülmen), Visbeck, Marienkapelle -- 2010.jpg",
            "type": "mediainfo",
        }

        validate_type(entry, model=SnapshotEntry)
