"""Action queue for batching multiple action executions into single API calls."""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Callable, Coroutine, Generator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pyoverkiz.models import Action

if TYPE_CHECKING:
    from pyoverkiz.enums import ExecutionMode


@dataclass(frozen=True, slots=True)
class ActionQueueSettings:
    """Settings for configuring the action queue behavior."""

    delay: float = 0.5
    max_actions: int = 20

    def validate(self) -> None:
        """Validate configuration values for the action queue."""
        if self.delay <= 0:
            raise ValueError(f"action_queue_delay must be positive, got {self.delay!r}")
        if self.max_actions < 1:
            raise ValueError(
                f"action_queue_max_actions must be at least 1, got {self.max_actions!r}"
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
    - The execution mode changes
    - The label changes
    - Manual flush is requested
    """

    def __init__(
        self,
        executor: Callable[
            [list[Action], ExecutionMode | None, str | None], Coroutine[None, None, str]
        ],
        settings: ActionQueueSettings | None = None,
    ) -> None:
        """Initialize the action queue.

        :param executor: Async function to execute batched actions
        :param settings: Queue configuration (uses defaults if None)
        """
        self._executor = executor
        self._settings = settings or ActionQueueSettings()

        self._pending_actions: list[Action] = []
        self._pending_mode: ExecutionMode | None = None
        self._pending_label: str | None = None
        self._pending_waiters: list[QueuedExecution] = []

        self._flush_task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()

    @staticmethod
    def _merge_actions(
        target: list[Action],
        index: dict[str, Action],
        source: list[Action],
        *,
        copy: bool = False,
    ) -> None:
        """Merge *source* actions into *target*, combining commands for duplicate devices."""
        for action in source:
            existing = index.get(action.device_url)
            if existing is None:
                merged = (
                    Action(device_url=action.device_url, commands=list(action.commands))
                    if copy
                    else action
                )
                target.append(merged)
                index[action.device_url] = merged
            else:
                existing.commands.extend(action.commands)

    async def add(
        self,
        actions: list[Action],
        mode: ExecutionMode | None = None,
        label: str | None = None,
    ) -> QueuedExecution:
        """Add actions to the queue.

        When multiple actions target the same device, their commands are merged
        into a single action to respect the gateway limitation of one action per
        device in each action group.

        Args:
            actions: Actions to queue.
            mode: Execution mode, which triggers a flush if it differs from the
                pending mode.
            label: Label for the action group.

        Returns:
            A `QueuedExecution` that resolves to the `exec_id` when the batch
            executes.
        """
        batches_to_execute: list[
            tuple[list[Action], ExecutionMode | None, str | None, list[QueuedExecution]]
        ] = []

        if not actions:
            raise ValueError("actions must contain at least one Action")

        normalized_actions: list[Action] = []
        normalized_index: dict[str, Action] = {}
        self._merge_actions(normalized_actions, normalized_index, actions, copy=True)

        async with self._lock:
            # If mode or label changes, flush existing queue first
            if self._pending_actions and (
                mode != self._pending_mode or label != self._pending_label
            ):
                batches_to_execute.append(self._prepare_flush())

            pending_index = {a.device_url: a for a in self._pending_actions}
            self._merge_actions(
                self._pending_actions, pending_index, normalized_actions
            )
            self._pending_mode = mode
            self._pending_label = label

            # Create waiter for this caller. This waiter is added to the current
            # batch being built, even if we flushed a previous batch above due to
            # a mode/label change. This ensures the waiter belongs to the batch
            # containing the actions we just added.
            waiter = QueuedExecution()
            self._pending_waiters.append(waiter)

            # If we hit max actions, flush immediately
            if len(self._pending_actions) >= self._settings.max_actions:
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
        await asyncio.sleep(self._settings.delay)
        async with self._lock:
            self._flush_task = None
            # Another coroutine may have already flushed the queue before we acquired the lock.
            actions, mode, label, waiters = self._prepare_flush()
            if not actions:
                return

        await self._execute_batch(actions, mode, label, waiters)

    def _prepare_flush(
        self,
    ) -> tuple[list[Action], ExecutionMode | None, str | None, list[QueuedExecution]]:
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
        mode: ExecutionMode | None,
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
        except asyncio.CancelledError as exc:
            # Propagate cancellation to all waiters, then re-raise.
            for waiter in waiters:
                waiter.set_exception(exc)
            raise
        except Exception as exc:  # noqa: BLE001
            # Propagate exceptions to all waiters without swallowing system-level exits.
            for waiter in waiters:
                waiter.set_exception(exc)

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
        value for critical control flow or for making flush decisions.
        """
        return len(self._pending_actions)

    async def shutdown(self) -> None:
        """Shutdown the queue, flushing any pending actions."""
        cancelled_task: asyncio.Task[None] | None = None
        batch_to_execute = None
        async with self._lock:
            if self._flush_task and not self._flush_task.done():
                cancelled_task = self._flush_task
                cancelled_task.cancel()
                self._flush_task = None

            if self._pending_actions:
                batch_to_execute = self._prepare_flush()

        if cancelled_task:
            with contextlib.suppress(asyncio.CancelledError):
                await cancelled_task

        if batch_to_execute:
            await self._execute_batch(*batch_to_execute)
