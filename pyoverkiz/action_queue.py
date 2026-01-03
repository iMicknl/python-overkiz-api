"""Action queue for batching multiple action executions into single API calls."""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyoverkiz.enums import CommandMode
    from pyoverkiz.models import Action


class QueuedExecution:
    """Represents a queued action execution that will resolve to an exec_id when the batch executes."""

    def __init__(self) -> None:
        """Initialize the queued execution."""
        self._future: asyncio.Future[str] = asyncio.Future()

    def set_result(self, exec_id: str) -> None:
        """Set the execution ID result."""
        if not self._future.done():
            self._future.set_result(exec_id)

    def set_exception(self, exception: BaseException) -> None:
        """Set an exception if the batch execution failed."""
        if not self._future.done():
            self._future.set_exception(exception)

    def is_done(self) -> bool:
        """Check if the execution has completed (either with result or exception)."""
        return self._future.done()

    def __await__(self):
        """Make this awaitable."""
        return self._future.__await__()


class ActionQueue:
    """Batches multiple action executions into single API calls.

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
        """Initialize the action queue.

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
        """Add actions to the queue.

        :param actions: Actions to queue
        :param mode: Command mode (will flush if different from pending mode)
        :param label: Label for the action group
        :return: QueuedExecution that resolves to exec_id when batch executes
        """
        batch_to_execute = None

        async with self._lock:
            # If mode or label changes, flush existing queue first
            if self._pending_actions and (
                mode != self._pending_mode or label != self._pending_label
            ):
                batch_to_execute = self._prepare_flush()

            # Add actions to pending queue
            self._pending_actions.extend(actions)
            self._pending_mode = mode
            self._pending_label = label

            # Create waiter for this caller. This waiter is added to the current
            # batch being built, even if we flushed a previous batch above due to
            # a mode/label change. This ensures the waiter belongs to the batch
            # containing the actions we just added.
            waiter = QueuedExecution()
            self._pending_waiters.append(waiter)

            # If we hit max actions, flush immediately
            if len(self._pending_actions) >= self._max_actions:
                # Prepare the current batch for flushing (which includes the actions
                # we just added). If we already flushed due to mode change, this is
                # a second batch.
                new_batch = self._prepare_flush()
                # Execute the first batch if it exists, then the second
                if batch_to_execute:
                    await self._execute_batch(*batch_to_execute)
                batch_to_execute = new_batch
            elif self._flush_task is None or self._flush_task.done():
                # Schedule delayed flush if not already scheduled
                self._flush_task = asyncio.create_task(self._delayed_flush())

        # Execute batch outside the lock if we flushed
        if batch_to_execute:
            await self._execute_batch(*batch_to_execute)

        return waiter

    async def _delayed_flush(self) -> None:
        """Wait for the delay period, then flush the queue."""
        waiters: list[QueuedExecution] = []
        try:
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
        except asyncio.CancelledError as exc:
            # Ensure all waiters are notified if this task is cancelled
            for waiter in waiters:
                waiter.set_exception(exc)
            raise

    def _prepare_flush(
        self,
    ) -> tuple[list[Action], CommandMode | None, str | None, list[QueuedExecution]]:
        """Prepare a flush by taking snapshot and clearing state (must be called with lock held).

        Returns a tuple of (actions, mode, label, waiters) that should be executed
        outside the lock using _execute_batch().
        """
        if not self._pending_actions:
            return ([], None, None, [])

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

        return (actions, mode, label, waiters)

    async def _execute_batch(
        self,
        actions: list[Action],
        mode: CommandMode | None,
        label: str | None,
        waiters: list[QueuedExecution],
    ) -> None:
        """Execute a batch of actions and notify waiters (must be called without lock)."""
        if not actions:
            return

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

    async def flush(self) -> None:
        """Force flush all pending actions immediately.

        This method forces the queue to execute any pending batched actions
        without waiting for the delay timer. The execution results are delivered
        to the corresponding QueuedExecution objects returned by add().

        This method is useful for forcing immediate execution without having to
        wait for the delay timer to expire.
        """
        batch_to_execute = None
        async with self._lock:
            if self._pending_actions:
                batch_to_execute = self._prepare_flush()

        # Execute outside the lock
        if batch_to_execute:
            await self._execute_batch(*batch_to_execute)

    def get_pending_count(self) -> int:
        """Get the (approximate) number of actions currently waiting in the queue.

        This method does not acquire the internal lock and therefore returns a
        best-effort snapshot that may be slightly out of date if the queue is
        being modified concurrently by other coroutines.
        """
        return len(self._pending_actions)

    async def shutdown(self) -> None:
        """Shutdown the queue, flushing any pending actions."""
        batch_to_execute = None
        async with self._lock:
            if self._flush_task and not self._flush_task.done():
                task = self._flush_task
                task.cancel()
                self._flush_task = None
                # Wait for cancellation to complete
                with contextlib.suppress(asyncio.CancelledError):
                    await task

            if self._pending_actions:
                batch_to_execute = self._prepare_flush()

        # Execute outside the lock
        if batch_to_execute:
            await self._execute_batch(*batch_to_execute)
