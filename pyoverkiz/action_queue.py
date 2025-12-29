"""Action queue for batching multiple action executions into single API calls."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyoverkiz.enums import CommandMode
    from pyoverkiz.models import Action


class QueuedExecution:
    """Represents a queued action execution that will resolve to an exec_id when the batch executes."""

    def __init__(self) -> None:
        self._future: asyncio.Future[str] = asyncio.Future()

    def set_result(self, exec_id: str) -> None:
        """Set the execution ID result."""
        if not self._future.done():
            self._future.set_result(exec_id)

    def set_exception(self, exception: Exception) -> None:
        """Set an exception if the batch execution failed."""
        if not self._future.done():
            self._future.set_exception(exception)

    def __await__(self):
        """Make this awaitable."""
        return self._future.__await__()


class ActionQueue:
    """
    Batches multiple action executions into single API calls.

    When actions are added, they are held for a configurable delay period.
    If more actions arrive during this window, they are batched together.
    The batch is flushed when:
    - The delay timer expires
    - The max actions limit is reached
    - The command mode changes
    - Manual flush is requested
    """

    def __init__(
        self,
        executor: Callable[
            [list[Action], CommandMode | None, str | None], Coroutine[None, None, str]
        ],
        delay: float = 0.5,
        max_actions: int = 20,
    ) -> None:
        """
        Initialize the action queue.

        :param executor: Async function to execute batched actions
        :param delay: Seconds to wait before auto-flushing (default 0.5)
        :param max_actions: Maximum actions per batch before forced flush (default 20)
        """
        self._executor = executor
        self._delay = delay
        self._max_actions = max_actions

        self._pending_actions: list[Action] = []
        self._pending_mode: CommandMode | None = None
        self._pending_label: str | None = None
        self._pending_waiters: list[QueuedExecution] = []

        self._flush_task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()

    async def add(
        self,
        actions: list[Action],
        mode: CommandMode | None = None,
        label: str | None = None,
    ) -> QueuedExecution:
        """
        Add actions to the queue.

        :param actions: Actions to queue
        :param mode: Command mode (will flush if different from pending mode)
        :param label: Label for the action group
        :return: QueuedExecution that resolves to exec_id when batch executes
        """
        async with self._lock:
            # If mode or label changes, flush existing queue first
            if self._pending_actions and (
                mode != self._pending_mode or label != self._pending_label
            ):
                await self._flush_now()

            # Add actions to pending queue
            self._pending_actions.extend(actions)
            self._pending_mode = mode
            self._pending_label = label

            # Create waiter for this caller
            waiter = QueuedExecution()
            self._pending_waiters.append(waiter)

            # If we hit max actions, flush immediately
            if len(self._pending_actions) >= self._max_actions:
                await self._flush_now()
            else:
                # Schedule delayed flush if not already scheduled
                if self._flush_task is None or self._flush_task.done():
                    self._flush_task = asyncio.create_task(self._delayed_flush())

            return waiter

    async def _delayed_flush(self) -> None:
        """Wait for the delay period, then flush the queue."""
        await asyncio.sleep(self._delay)
        async with self._lock:
            if not self._pending_actions:
                return

            # Take snapshot and clear state while holding lock
            actions = self._pending_actions
            mode = self._pending_mode
            label = self._pending_label
            waiters = self._pending_waiters

            self._pending_actions = []
            self._pending_mode = None
            self._pending_label = None
            self._pending_waiters = []
            self._flush_task = None

        # Execute outside the lock
        try:
            exec_id = await self._executor(actions, mode, label)
            for waiter in waiters:
                waiter.set_result(exec_id)
        except Exception as exc:
            for waiter in waiters:
                waiter.set_exception(exc)

    async def _flush_now(self) -> None:
        """Execute pending actions immediately (must be called with lock held)."""
        if not self._pending_actions:
            return

        # Cancel any pending flush task
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
        self._flush_task = None

        # Take snapshot of current batch
        actions = self._pending_actions
        mode = self._pending_mode
        label = self._pending_label
        waiters = self._pending_waiters

        # Clear pending state
        self._pending_actions = []
        self._pending_mode = None
        self._pending_label = None
        self._pending_waiters = []

        # Execute the batch (must release lock before calling executor to avoid deadlock)
        # Note: This is called within a lock context, we'll execute outside
        try:
            exec_id = await self._executor(actions, mode, label)
            # Notify all waiters
            for waiter in waiters:
                waiter.set_result(exec_id)
        except Exception as exc:
            # Propagate exception to all waiters
            for waiter in waiters:
                waiter.set_exception(exc)
            raise

    async def flush(self) -> list[str]:
        """
        Force flush all pending actions immediately.

        :return: List of exec_ids from flushed batches
        """
        async with self._lock:
            if not self._pending_actions:
                return []

            # Since we can only have one batch pending at a time,
            # this will return a single exec_id in a list
            exec_ids: list[str] = []

            try:
                await self._flush_now()
                # If flush succeeded, we can't actually return the exec_id here
                # since it's delivered via the waiters. This method is mainly
                # for forcing a flush, not retrieving results.
                # Return empty list to indicate flush completed
            except Exception:
                # If flush fails, the exception will be propagated to waiters
                # and also raised here
                raise

            return exec_ids

    def get_pending_count(self) -> int:
        """Get the number of actions currently waiting in the queue."""
        return len(self._pending_actions)

    async def shutdown(self) -> None:
        """Shutdown the queue, flushing any pending actions."""
        async with self._lock:
            if self._flush_task and not self._flush_task.done():
                self._flush_task.cancel()
                self._flush_task = None

            if self._pending_actions:
                await self._flush_now()
