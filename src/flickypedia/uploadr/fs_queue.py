"""
This file provides a basic implementation of a task queue.

At one point we were using Celery [1], which is a very powerful and
well-established job queue for Python, but it's way more than we need
for Flickypedia -- and somewhat tricky to debug.

If we need to extend or modify this module, we should reconsider the
decision to do a DIY task queue rather than using a prebuilt library --
but for now this seems good enough for our purposes.

Note: the locking in this module is somewhat primitive, and relies on
the filesystem.  See the comments in ``process_single_task()``.

[1]: https://docs.celeryq.dev/en/stable/

"""

import abc
import datetime
import json
import logging
import os
import pathlib
import time
from typing import Generic, Literal, TypedDict, TypeVar
import uuid

from flickypedia.utils import DatetimeDecoder, DatetimeEncoder, validate_typeddict


In = TypeVar("In")
Out = TypeVar("Out")


State = Literal["waiting", "in_progress", "failed", "completed"]


class TaskEvent(TypedDict):
    time: datetime.datetime
    description: str


class Task(TypedDict, Generic[In, Out]):
    id: str
    events: list[TaskEvent]
    state: State
    task_input: In
    task_output: Out


class AbstractFilesystemTaskQueue(abc.ABC, Generic[In, Out]):
    """
    A basic task queue based on the file system.

    This is designed for single-instance, low-volume tasks.  A task
    can be in one of four states, and moves through the states as
    follows:

                +-------------+
                |   waiting   |
                +-------------+
                       |
                       v
                +-------------+
                | in progress |
                +-------------+
                       |
              +--------+--------+
              |                 |
              v                 v
        +-----------+     +----------+
        | completed |     |  failed  |
        +-----------+     +----------+

    Each task is stored in a single file.  Each of these states
    represents a single folder.  The state of a task is the folder
    that it's in.

    e.g. when a task is created, that becomes a task in the "waiting"
    folder.  When the task is being worked on, it moves to "in progress".
    Finally, it moves to "completed/failed" depending on its final state.

    This class writes logs to ``queue.log`` inside the base directory.

    """

    def __init__(self, *, base_dir: pathlib.Path) -> None:
        self.base_dir = base_dir

        for dirname in self.directories:
            os.makedirs(dirname, exist_ok=True)

        self.logger = logging.getLogger(name=str(base_dir))
        self.configure_logger()

    @property
    def logfile_path(self) -> pathlib.Path:
        return self.base_dir / "queue.log"

    def configure_logger(self) -> None:
        self.logger.setLevel(level=logging.DEBUG)

        pid = os.getpid()

        handler = logging.FileHandler(filename=self.logfile_path)
        handler.setFormatter(
            fmt=logging.Formatter(f"%(asctime)s - {pid} - %(levelname)s - %(message)s")
        )

        self.logger.addHandler(handler)

    @property
    def directories(self) -> set[pathlib.Path]:
        return {
            self.waiting_dir,
            self.in_progress_dir,
            self.failed_dir,
            self.completed_dir,
            self.tmp_dir,
        }

    @property
    def waiting_dir(self) -> pathlib.Path:
        return self.base_dir / "waiting"

    @property
    def in_progress_dir(self) -> pathlib.Path:
        return self.base_dir / "in_progress"

    @property
    def failed_dir(self) -> pathlib.Path:
        return self.base_dir / "failed"

    @property
    def completed_dir(self) -> pathlib.Path:
        return self.base_dir / "completed"

    @property
    def tmp_dir(self) -> pathlib.Path:
        return self.base_dir / "tmp"

    def write_task(self, task: Task[In, Out]) -> None:
        """
        Persist information about a task to disk.

        Tasks are saved as JSON files.  We write and rename the files
        atomically, which means there's always a single, valid file
        describing the task on disk.
        """
        filename = task["id"]

        tmp_path = self.tmp_dir / filename
        out_path = self.base_dir / task["state"] / filename

        # The use of exclusive file mode "x" means we'll throw if this
        # tmp file already exists -- this seems unlikely, but might
        # indicate another process is working on this file.
        with open(tmp_path, "x") as tmp_file:
            tmp_file.write(json.dumps(task, cls=DatetimeEncoder))

        # If the task is changing state, we need to make sure we remove
        # the task in the previous folder.
        #
        # e.g. if the task is going from 'waiting' to 'in progress',
        # we first update the file in 'waiting', then we move that file
        # into 'in progress'.
        #
        # If the task isn't changing state, we just update the file
        # in the current folder.
        #
        # Note that ``os.rename()`` is atomic, which is how we get
        # atomic-like file writes.
        try:
            prior_task = self.read_task(task_id=task["id"])
        except ValueError:
            prior_task = None

        if prior_task is not None and prior_task["state"] != task["state"]:
            prior_path = self.base_dir / prior_task["state"] / filename
            os.rename(tmp_path, prior_path)
            os.rename(prior_path, out_path)
        else:
            os.rename(tmp_path, out_path)

    def read_task(self, task_id: str) -> Task[In, Out]:
        """
        Return the state of a currently running task.
        """
        for dirname in [
            self.waiting_dir,
            self.in_progress_dir,
            self.failed_dir,
            self.completed_dir,
        ]:
            try:
                with open(dirname / task_id) as in_file:
                    t = json.load(in_file, cls=DatetimeDecoder)
                    return validate_typeddict(t, model=Task[In, Out])
            except FileNotFoundError:
                pass

        raise ValueError(f"Could not find task with ID {task_id}")

    def start_task(
        self,
        task_input: In,
        task_output: Out,
        task_id: str | None = None,
    ) -> str:
        """
        Creates a new task.  Returns the task ID.
        """
        task_id = task_id or str(uuid.uuid4())

        self.logger.info("Creating task %s", task_id)

        self.write_task(
            task={
                "id": task_id,
                "events": [
                    {"time": datetime.datetime.now(), "description": "Task created"}
                ],
                "state": "waiting",
                "task_input": task_input,
                "task_output": task_output,
            }
        )

        return task_id

    def record_task_event(
        self, task: Task[In, Out], *, state: State | None = None, event: str
    ) -> None:
        """
        Record some event occurring on a task.

        This is useful for per-task logging.
        """
        if state is not None:
            task["state"] = state

        task["events"].append({"time": datetime.datetime.now(), "description": event})

        self.write_task(task)

    def _next_available_task(self) -> str | None:
        """
        Returns the ID of the next available task (if any).
        """
        # A list of tuples (filename, modified time)
        candidates = []

        for filename in os.listdir(self.waiting_dir):
            try:
                candidates.append(
                    (filename, os.path.getmtime(self.waiting_dir / filename))
                )
            except FileNotFoundError:
                pass

        try:
            filename, _ = min(candidates, key=lambda fm: fm[1])
            return filename
        except ValueError:
            return None

    def process_single_task(self) -> str | None:
        """
        Process the next available task.

        Returns the ID of the task that was processed, if any.
        """
        this_task_id = self._next_available_task()

        # If there wasn't a next task, we assume the queue is empty
        # and wait for 1 second before looking again.
        if this_task_id is None:
            self.logger.debug("No tasks found, sleeping for 1 second...")
            time.sleep(1)
            return None

        # Atomically move the task from "waiting" to "in progress".
        # This will make the task unavailable for other processes
        # and only available to this process.
        #
        # If two processes try to rename the same file at once, only
        # one of them will succeed in doing so -- the other will get
        # a FileNotFoundError.
        #
        # This is a basic locking system -- only one process can own
        # the rename, and that's the process that "locks" this task.
        #
        # We may need something more sophisticated eventually, but I've
        # used this approach pretty successfully for large queues on
        # single machines before.
        self.logger.info("Task %s: starting work", this_task_id)

        try:
            os.rename(
                src=self.waiting_dir / this_task_id,
                dst=self.in_progress_dir / this_task_id,
            )
        except FileNotFoundError:
            self.logger.warning(
                "Task %s: file not found, assuming picked up by another worker",
                this_task_id,
            )
            return None

        # Now actually start working on the task.
        task = self.read_task(task_id=this_task_id)

        self.record_task_event(task, state="in_progress", event="Task started")

        try:
            self.process_individual_task(task)
        except Exception as exc:
            self.logger.error(
                "Task %s: task failed with exception %r", this_task_id, exc
            )

            self.record_task_event(
                task, state="failed", event=f"Task failed with an exception: {exc}"
            )
        else:
            self.logger.info("Task %s: task completed without exception", this_task_id)

            self.record_task_event(
                task, state="completed", event="Task completed without exception"
            )

        return task["id"]

    def process_tasks(self) -> None:  # pragma: no cover
        """
        Keep looking for new tasks, and when found, start working on them.
        """
        print(f"Looking for tasks in {self.base_dir}...")
        print(f"Follow the log at {self.logfile_path}")

        self.logger.info("Starting looking for tasks in the queue...")

        while True:
            self.process_single_task()

    @abc.abstractmethod
    def process_individual_task(self, t: Task[In, Out]) -> None:
        pass
