import os
from typing import Generator
import uuid

from flask import Flask
import pytest

from flickypedia.uploadr.tasks import ProgressTracker


@pytest.fixture
def tracker(app: Flask) -> Generator[ProgressTracker, None, None]:
    t = ProgressTracker(task_id=str(uuid.uuid4()))
    yield t

    try:
        os.unlink(t.path)
    except FileNotFoundError:  # pragma: no cover
        pass


def test_progress_tracker(tracker: ProgressTracker) -> None:
    assert tracker.get_progress() is None

    update_1 = {"time": 1, "event": "start task"}
    tracker.record_progress(data=update_1)
    assert tracker.get_progress() == update_1

    update_2 = {"time": 2, "event": "continue task"}
    tracker.record_progress(data=update_2)
    assert tracker.get_progress() == update_2
