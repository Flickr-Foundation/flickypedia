import pathlib

from flickypedia.uploadr.fs_queue import AbstractFilesystemTaskQueue, Task


class AddingQueue(AbstractFilesystemTaskQueue):
    """
    A simple queue that takes a list of integers as inputs and adds
    them together.
    """

    def start_task(self, task_input: list[int]) -> str:
        return super().start_task(task_input)

    def process_individual_task(self, task: Task) -> None:
        task["data"] = sum(task["data"])
        task["state"] = "completed"
        self.write_task(task)


def test_queue(tmp_path: pathlib.Path) -> None:
    q = AddingQueue(base_dir=tmp_path)

    task_id = q.start_task(task_input=[1, 2, 3])
    q.process_single_task()

    task = q.read_task(task_id=task_id)

    assert task["id"] == task_id
    assert task["state"] == "completed"
    assert task["data"] == 6
