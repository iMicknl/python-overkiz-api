"""Action queue for batching multiple action executions into single API calls."""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Callable, Coroutine, Generator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyoverkiz.enums import CommandMode
    from pyoverkiz.models import Action


@dataclass(frozen=True, slots=True)
class ActionQueueSettings:
    """Settings for configuring the action queue behavior."""

    delay: float = 0.5
    max_actions: int = 20

    def validate(self) -> None:
        """Validate configuration values for the action queue."""
        if self.delay <= 0:
            raise ValueError(f"action_queue.delay must be positive, got {self.delay!r}")
        if self.max_actions < 1:
            raise ValueError(
                f"action_queue.max_actions must be at least 1, got {self.max_actions!r}"
            )


class QueuedExecution:
    """Represents a queued action execution that will resolve to an exec_id when the batch executes."""

    def __init__(self) -> None:
        """Initialize the queued execution."""
        # Future is created lazily to ensure it is bound to the running event loop.
        # Creating it in __init__ would fail if no loop is running yet.
        self._future: asyncio.Future[str] | None = None

    def _ensure_future(self) -> asyncio.Future[str]:
        """Create the underlying future lazily, bound to the running event loop."""
        # This method is the single point of future creation to guarantee
        # consistent loop binding for callers that await or set results later.
        if self._future is None:
            loop = asyncio.get_running_loop()
            self._future = loop.create_future()
        return self._future

    def set_result(self, exec_id: str) -> None:
        """Set the execution ID result."""
        future = self._ensure_future()
        if not future.done():
            future.set_result(exec_id)

    def set_exception(self, exception: BaseException) -> None:
        """Set an exception if the batch execution failed."""
        future = self._ensure_future()
        if not future.done():
            future.set_exception(exception)

    def is_done(self) -> bool:
        """Check if the execution has completed (either with result or exception)."""
        return self._future.done() if self._future is not None else False

    def __await__(self) -> Generator[Any, None, str]:
        """Make this awaitable."""
        return self._ensure_future().__await__()


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

        When multiple actions target the same device, their commands are merged
        into a single action to respect the gateway limitation of one action per
        device in each action group.

        :param actions: Actions to queue
        :param mode: Command mode (will flush if different from pending mode)
        :param label: Label for the action group
        :return: QueuedExecution that resolves to exec_id when batch executes
        """
        batches_to_execute: list[
            tuple[list[Action], CommandMode | None, str | None, list[QueuedExecution]]
        ] = []

        if not actions:
            raise ValueError("actions must contain at least one Action")

        normalized_actions: list[Action] = []
        normalized_index: dict[str, Action] = {}
        for action in actions:
            existing = normalized_index.get(action.device_url)
            if existing is None:
                normalized_actions.append(action)
                normalized_index[action.device_url] = action
            else:
                existing.commands.extend(action.commands)

        async with self._lock:
            # If mode or label changes, flush existing queue first
            if self._pending_actions and (
                mode != self._pending_mode or label != self._pending_label
            ):
                batches_to_execute.append(self._prepare_flush())

            # Add actions to pending queue
            for action in normalized_actions:
                pending = next(
                    (
                        pending_action
                        for pending_action in self._pending_actions
                        if pending_action.device_url == action.device_url
                    ),
                    None,
                )
                if pending is None:
                    self._pending_actions.append(action)
                else:
                    pending.commands.extend(action.commands)
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
                batches_to_execute.append(self._prepare_flush())
            elif self._flush_task is None or self._flush_task.done():
                # Schedule delayed flush if not already scheduled
                self._flush_task = asyncio.create_task(self._delayed_flush())

        # Execute batches outside the lock if we flushed
        for batch in batches_to_execute:
            if batch[0]:
                await self._execute_batch(*batch)

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
            await self._execute_batch(actions, mode, label, waiters)
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
        except BaseException as exc:
            # Propagate exception to all waiters
            for waiter in waiters:
                waiter.set_exception(exc)
            if isinstance(exc, asyncio.CancelledError):
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
        being modified concurrently by other coroutines. Do not rely on this
        value for critical control flow.
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
