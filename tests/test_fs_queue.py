import collections
import concurrent.futures
import pathlib
import traceback

import pytest

from flickypedia.fs_queue import AbstractFilesystemTaskQueue, Task


NumberTask = Task[list[int], int]
NumberQueue = AbstractFilesystemTaskQueue[list[int], int]


class AddingQueue(NumberQueue):
    """
    A simple queue that takes a list of integers as inputs and adds
    them together.
    """

    def process_individual_task(self, task: NumberTask) -> None:
        task["task_output"] = sum(task["task_input"])
        task["state"] = "completed"

        self.record_task_event(task, event="Added two integers together!")

        self.write_task(task)


class FailingQueue(NumberQueue):
    """
    A queue that throws an exception rather than do anything.
    """

    def process_individual_task(self, task: NumberTask) -> None:
        raise ValueError("BOOM!")


@pytest.fixture
def queue(tmp_path: pathlib.Path) -> AddingQueue:
    return AddingQueue(base_dir=tmp_path)


def test_can_process_a_single_message(queue: AddingQueue) -> None:
    task_id = queue.start_task(task_input=[1, 2, 3], task_output=-1)
    queue.process_single_task()

    task = queue.read_task(task_id=task_id)

    assert task["id"] == task_id
    assert task["state"] == "completed"
    assert task["task_output"] == 6

    descriptions = [ev["description"] for ev in task["events"]]
    assert descriptions == [
        "Task created",
        "Task started",
        "Added two integers together!",
        "Task completed without exception",
    ]


def test_no_available_tasks_is_fine(queue: AddingQueue) -> None:
    queue.process_single_task()


def test_multiple_workers_on_same_queue_is_fine(queue: AddingQueue) -> None:
    """
    If multiple workers are processing the same queue, and a message
    arrives, exactly one of them should pick it up.

    The others should either miss it, or decline when they find its
    "locked" by the other process.
    """
    task_id = queue.start_task(task_input=[1, 2, 3], task_output=-1)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(queue.process_single_task) for _ in range(10)}

        done, not_done = concurrent.futures.wait(futures)
        assert len(not_done) == 0
        assert all(fut.done() for fut in done)

        # This isn't part of the test, but I've seen the following assertion
        # fail a few times with an unexpected FileNotFoundError.
        #
        # If/when that recurs, this branch is meant to provide debugging
        # information so I can isolate and properly fix that exception.
        for fut in done:  # pragma: no cover
            if fut.exception() is not None:
                print(traceback.print_exception(fut.exception()))

        assert all(fut.exception() is None for fut in done), [
            fut.exception() for fut in done
        ]

        # The process_single_task() method returns the ID of the task
        # it processed, if any.
        #
        # Exactly one of the processes should claim to have processed
        # this task.
        assert collections.Counter(fut.result() for fut in done) == {
            task_id: 1,
            None: 9,
        }


def test_handles_failure_in_the_process_method(tmp_path: pathlib.Path) -> None:
    failing_queue = FailingQueue(base_dir=tmp_path)

    task_id = failing_queue.start_task(task_input=[1, 2, 3], task_output=-1)

    failing_queue.process_single_task()

    task = failing_queue.read_task(task_id=task_id)

    assert task["id"] == task_id
    assert task["state"] == "failed"
    assert task["task_output"] == -1

    descriptions = [ev["description"] for ev in task["events"]]
    assert descriptions == [
        "Task created",
        "Task started",
        "Task failed with an exception: BOOM!",
    ]
