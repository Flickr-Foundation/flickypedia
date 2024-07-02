import concurrent.futures
import os
import pathlib
import random
import typing

import tqdm

from .actions import Action
from .backfillr import Backfillr
from flickypedia.fs_queue import AbstractFilesystemTaskQueue, Task


class BackfillrBatchResult(typing.TypedDict):
    filename: list[str]
    actions: dict[str, list[Action]]


class BackfillrQueue(AbstractFilesystemTaskQueue[list[str], BackfillrBatchResult]):
    def __init__(self, *, backfillr: Backfillr | None, base_dir: pathlib.Path) -> None:
        self.backfillr = backfillr
        super().__init__(base_dir=base_dir)

    def _next_available_task(self) -> str | None:
        """
        Returns the ID of the next available task (if any).
        """
        try:
            return random.choice(os.listdir(self.waiting_dir))
        except IndexError:
            return None

    def process_individual_task(self, task: Task[list[str], BackfillrBatchResult]) -> None:
        task['state'] = 'in_progress'

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self.backfillr.update_file, filename=filename): filename
                for filename in task['task_input']
                if not task['task_output'][filename]
            }

            for i, fut in enumerate(concurrent.futures.as_completed(futures)):
                filename = futures[fut]
                actions = fut.result()

                task['task_output'][filename] = [
                    {'property_id': a['property_id'], 'action': a['action']} for a in actions
                ]
                self.record_task_event(
                    task, event=f'Successfully processed {filename!r}'
                )

        task['state'] = 'completed'
