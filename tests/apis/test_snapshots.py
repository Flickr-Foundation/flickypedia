import pathlib

from flickypedia.apis.snapshots import parse_sdc_snapshot


def test_parse_sdc_snapshot() -> None:
    """
    The snapshot in this test was obtained by slicing a couple of lines
    from the real 20231207 snapshot.
    """
    snapshot_path = pathlib.Path(
        "tests/fixtures/commons-20231207-mediainfo.slice.json.bz2"
    )

    assert len(list(parse_sdc_snapshot(snapshot_path))) == 2
