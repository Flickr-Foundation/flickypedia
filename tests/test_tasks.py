import os
import uuid

import pytest

from flickypedia.tasks import ProgressTracker


@pytest.fixture
def tracker():
    t = ProgressTracker(task_id=str(uuid.uuid4()))
    yield t

    try:
        os.unlink(t.path)
    except FileNotFoundError:
        pass


def test_progress_tracker(tracker):
    assert tracker.get_progress() is None