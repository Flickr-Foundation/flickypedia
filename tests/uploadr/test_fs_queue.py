import contextlib
import os
import pathlib
import subprocess
import textwrap
import time
import uuid

from flickypedia.uploadr.fs_queue import AddingQueue


@contextlib.contextmanager
def queue_worker(tmp_path: pathlib.Path):
    out_path = os.path.join(tmpdir, f"worker-{uuid.uuid4()}.py")

    with open(out_path, "w") as out_file:
        out_file.write(
            textwrap.dedent(
                """
        from flickypedia.uploadr.fs_queue import AddingQueue

        q = AddingQueue()
        q.process_tasks()
        """
            ).strip()
        )

    proc = subprocess.Popen(["python3", out_path])

    yield proc

    proc.terminate()
    proc.wait(timeout=1)


def test_queue(tmp_path: pathlib.Path) -> None:
    q = AddingQueue(base_dir=tmpdir)

    with queue_worker(tmpdir) as worker:
        task_id = q.start_task(task_input=[1, 2, 3])
        time.sleep(1)

        task = q.read_task(task_id=task_id)

        from pprint import pprint

        pprint(task)

    # print(repr(open(f'{tmpdir}/worker.py').read()))
