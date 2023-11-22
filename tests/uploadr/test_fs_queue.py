import contextlib
import concurrent.futures
import os
import pathlib
import subprocess
import textwrap
import time
import uuid

from flickypedia.uploadr.fs_queue import AddingQueue


@contextlib.contextmanager
def queue_worker(tmp_path: pathlib.Path):
    out_path = tmp_path / f"worker-{uuid.uuid4()}.py"

    with open(out_path, "w") as out_file:
        out_file.write(
            textwrap.dedent(
                """
        from pathlib import *
        from flickypedia.uploadr.fs_queue import AddingQueue

        q = AddingQueue(base_dir=%r)
        q.process_tasks()
        """
                % tmp_path
            ).strip()
        )

    proc = subprocess.Popen(["python3", out_path])

    yield proc

    proc.terminate()
    proc.wait(timeout=1)


from multiprocessing import Process


def test_queue(tmp_path: pathlib.Path) -> None:
    q = AddingQueue(base_dir=tmp_path)

    task_id = q.start_task(task_input=[1,2,3])
    q.process_single_task()

    task = q.read_task(task_id=task_id)

    assert task['id'] == task_id
    assert task['state'] == 'completed'
    assert task['data'] == 6
