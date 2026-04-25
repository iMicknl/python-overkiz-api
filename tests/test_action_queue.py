"""Tests for ActionQueue."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from pyoverkiz.action_queue import ActionQueue, ActionQueueSettings, QueuedExecution
from pyoverkiz.enums import ExecutionMode, OverkizCommand
from pyoverkiz.models import Action, Command


@pytest.fixture
def mock_executor():
    """Create a mock executor function."""

    async def executor(actions, mode, label):
        # Return immediately, no delay
        return f"exec-{len(actions)}-{mode}-{label}"

    return AsyncMock(side_effect=executor)


@pytest.mark.asyncio
async def test_action_queue_single_action(mock_executor):
    """Test queue with a single action."""
    queue = ActionQueue(executor=mock_executor, settings=ActionQueueSettings(delay=0.1))

    action = Action(
        device_url="io://1234-5678-9012/1",
        commands=[Command(name=OverkizCommand.CLOSE)],
    )

    queued = await queue.add([action])
    assert isinstance(queued, QueuedExecution)

    # Wait for the batch to execute
    exec_id = await queued
    assert exec_id.startswith("exec-1-")

    # Verify executor was called
    mock_executor.assert_called_once()


@pytest.mark.asyncio
async def test_action_queue_batching(mock_executor):
    """Test that multiple actions are batched together."""
    queue = ActionQueue(executor=mock_executor, settings=ActionQueueSettings(delay=0.2))

    actions = [
        Action(
            device_url=f"io://1234-5678-9012/{i}",
            commands=[Command(name=OverkizCommand.CLOSE)],
        )
        for i in range(3)
    ]

    # Add actions in quick succession
    queued1 = await queue.add([actions[0]])
    queued2 = await queue.add([actions[1]])
    queued3 = await queue.add([actions[2]])

    # All should return the same exec_id
    exec_id1 = await queued1
    exec_id2 = await queued2
    exec_id3 = await queued3

    assert exec_id1 == exec_id2 == exec_id3
    assert "exec-3-" in exec_id1  # 3 actions in batch

    # Executor should be called only once
    mock_executor.assert_called_once()


@pytest.mark.asyncio
async def test_action_queue_max_actions_flush(mock_executor):
    """Test that queue flushes when max actions is reached."""
    queue = ActionQueue(
        executor=mock_executor, settings=ActionQueueSettings(delay=10.0, max_actions=3)
    )

    actions = [
        Action(
            device_url=f"io://1234-5678-9012/{i}",
            commands=[Command(name=OverkizCommand.CLOSE)],
        )
        for i in range(5)
    ]

    # Add 3 actions - should trigger flush
    queued1 = await queue.add([actions[0]])
    queued2 = await queue.add([actions[1]])
    queued3 = await queue.add([actions[2]])

    # Wait a bit for flush to complete
    await asyncio.sleep(0.05)

    # First 3 should be done
    assert queued1.is_done()
    assert queued2.is_done()
    assert queued3.is_done()

    # Add 2 more - should start a new batch
    queued4 = await queue.add([actions[3]])
    queued5 = await queue.add([actions[4]])

    # Wait for second batch
    await queued4
    await queued5

    # Should have been called twice (2 batches)
    assert mock_executor.call_count == 2


@pytest.mark.asyncio
async def test_action_queue_mode_change_flush(mock_executor):
    """Test that queue flushes when command mode changes."""
    queue = ActionQueue(executor=mock_executor, settings=ActionQueueSettings(delay=0.5))

    action = Action(
        device_url="io://1234-5678-9012/1",
        commands=[Command(name=OverkizCommand.CLOSE)],
    )

    # Add action with normal mode
    queued1 = await queue.add([action], mode=None)

    # Add action with high priority - should flush previous batch
    queued2 = await queue.add([action], mode=ExecutionMode.HIGH_PRIORITY)

    # Wait for both batches
    exec_id1 = await queued1
    exec_id2 = await queued2

    # Should be different exec_ids (different batches)
    assert exec_id1 != exec_id2

    # Should have been called twice
    assert mock_executor.call_count == 2


@pytest.mark.asyncio
async def test_action_queue_label_change_flush(mock_executor):
    """Test that queue flushes when label changes."""
    queue = ActionQueue(executor=mock_executor, settings=ActionQueueSettings(delay=0.5))

    action = Action(
        device_url="io://1234-5678-9012/1",
        commands=[Command(name=OverkizCommand.CLOSE)],
    )

    # Add action with label1
    queued1 = await queue.add([action], label="label1")

    # Add action with label2 - should flush previous batch
    queued2 = await queue.add([action], label="label2")

    # Wait for both batches
    exec_id1 = await queued1
    exec_id2 = await queued2

    # Should be different exec_ids (different batches)
    assert exec_id1 != exec_id2

    # Should have been called twice
    assert mock_executor.call_count == 2


@pytest.mark.asyncio
async def test_action_queue_duplicate_device_merge(mock_executor):
    """Test that queue merges commands for duplicate devices."""
    queue = ActionQueue(executor=mock_executor, settings=ActionQueueSettings(delay=0.5))

    action1 = Action(
        device_url="io://1234-5678-9012/1",
        commands=[Command(name=OverkizCommand.CLOSE)],
    )
    action2 = Action(
        device_url="io://1234-5678-9012/1",
        commands=[Command(name=OverkizCommand.OPEN)],
    )

    queued1 = await queue.add([action1])
    queued2 = await queue.add([action2])

    exec_id1 = await queued1
    exec_id2 = await queued2

    assert exec_id1 == exec_id2
    mock_executor.assert_called_once()


@pytest.mark.asyncio
async def test_action_queue_duplicate_device_merge_order(mock_executor):
    """Test that command order is preserved when merging."""
    queue = ActionQueue(executor=mock_executor, settings=ActionQueueSettings(delay=0.1))

    action1 = Action(
        device_url="io://1234-5678-9012/1",
        commands=[Command(name=OverkizCommand.CLOSE)],
    )
    action2 = Action(
        device_url="io://1234-5678-9012/1",
        commands=[Command(name=OverkizCommand.OPEN)],
    )

    queued = await queue.add([action1, action2])
    await queued

    args, _ = mock_executor.call_args
    actions = args[0]
    assert len(actions) == 1
    assert [command.name for command in actions[0].commands] == [
        OverkizCommand.CLOSE,
        OverkizCommand.OPEN,
    ]


@pytest.mark.asyncio
async def test_action_queue_duplicate_device_merge_does_not_mutate_inputs(
    mock_executor,
):
    """Test that merge behavior does not mutate caller-owned Action commands."""
    queue = ActionQueue(executor=mock_executor, settings=ActionQueueSettings(delay=0.1))

    action1 = Action(
        device_url="io://1234-5678-9012/1",
        commands=[Command(name=OverkizCommand.CLOSE)],
    )
    action2 = Action(
        device_url="io://1234-5678-9012/1",
        commands=[Command(name=OverkizCommand.OPEN)],
    )

    queued = await queue.add([action1, action2])
    await queued

    assert [command.name for command in action1.commands] == [OverkizCommand.CLOSE]
    assert [command.name for command in action2.commands] == [OverkizCommand.OPEN]


@pytest.mark.asyncio
async def test_action_queue_manual_flush(mock_executor):
    """Test manual flush of the queue."""
    queue = ActionQueue(
        executor=mock_executor, settings=ActionQueueSettings(delay=10.0)
    )  # Long delay

    action = Action(
        device_url="io://1234-5678-9012/1",
        commands=[Command(name=OverkizCommand.CLOSE)],
    )

    queued = await queue.add([action])

    # Manually flush
    await queue.flush()

    # Should be done now
    assert queued.is_done()
    exec_id = await queued
    assert exec_id.startswith("exec-1-")


@pytest.mark.asyncio
async def test_action_queue_shutdown(mock_executor):
    """Test that shutdown flushes pending actions."""
    queue = ActionQueue(
        executor=mock_executor, settings=ActionQueueSettings(delay=10.0)
    )

    action = Action(
        device_url="io://1234-5678-9012/1",
        commands=[Command(name=OverkizCommand.CLOSE)],
    )

    queued = await queue.add([action])

    # Shutdown should flush
    await queue.shutdown()

    # Should be done
    assert queued.is_done()
    mock_executor.assert_called_once()


@pytest.mark.asyncio
async def test_action_queue_error_propagation(mock_executor):
    """Test that exceptions are propagated to all waiters."""
    # Make executor raise an exception
    mock_executor.side_effect = ValueError("API Error")

    queue = ActionQueue(executor=mock_executor, settings=ActionQueueSettings(delay=0.1))

    action = Action(
        device_url="io://1234-5678-9012/1",
        commands=[Command(name=OverkizCommand.CLOSE)],
    )

    queued1 = await queue.add([action])
    queued2 = await queue.add([action])

    # Both should raise the same exception
    with pytest.raises(ValueError, match="API Error"):
        await queued1

    with pytest.raises(ValueError, match="API Error"):
        await queued2


@pytest.mark.asyncio
async def test_action_queue_get_pending_count():
    """Test getting pending action count."""
    mock_executor = AsyncMock(return_value="exec-123")
    queue = ActionQueue(executor=mock_executor, settings=ActionQueueSettings(delay=0.5))

    assert queue.get_pending_count() == 0

    action = Action(
        device_url="io://1234-5678-9012/1",
        commands=[Command(name=OverkizCommand.CLOSE)],
    )

    await queue.add([action])
    assert queue.get_pending_count() == 1

    await queue.add([action])
    assert queue.get_pending_count() == 1

    # Wait for flush
    await asyncio.sleep(0.6)
    assert queue.get_pending_count() == 0


@pytest.mark.asyncio
async def test_queued_execution_awaitable():
    """Test that QueuedExecution is properly awaitable."""
    queued = QueuedExecution()

    # Set result in background
    async def set_result():
        await asyncio.sleep(0.05)
        queued.set_result("exec-123")

    task = asyncio.create_task(set_result())

    # Await the result
    result = await queued
    assert result == "exec-123"

    # Ensure background task has completed
    await task


@pytest.mark.asyncio
async def test_action_queue_settings_validate():
    """Test that validate raises on invalid settings."""
    with pytest.raises(ValueError, match="positive"):
        ActionQueueSettings(delay=-1).validate()

    with pytest.raises(ValueError, match="at least 1"):
        ActionQueueSettings(max_actions=0).validate()

    # Valid settings should not raise
    ActionQueueSettings(delay=0.5, max_actions=10).validate()


@pytest.mark.asyncio
async def test_action_queue_add_empty_actions(mock_executor):
    """Test that add raises ValueError for empty action list."""
    queue = ActionQueue(executor=mock_executor, settings=ActionQueueSettings(delay=0.1))

    with pytest.raises(ValueError, match="at least one Action"):
        await queue.add([])


@pytest.mark.asyncio
async def test_action_queue_executor_cancelled_propagates():
    """Test that CancelledError during execution propagates to waiters."""

    async def cancelling_executor(actions, mode, label):
        raise asyncio.CancelledError

    queue = ActionQueue(
        executor=AsyncMock(side_effect=cancelling_executor),
        settings=ActionQueueSettings(delay=0.05),
    )

    action = Action(
        device_url="io://1234-5678-9012/1",
        commands=[Command(name=OverkizCommand.CLOSE)],
    )

    queued = await queue.add([action])

    with pytest.raises(asyncio.CancelledError):
        await queued


@pytest.mark.asyncio
async def test_action_queue_flush_empty(mock_executor):
    """Test that flushing an empty queue is a no-op."""
    queue = ActionQueue(executor=mock_executor, settings=ActionQueueSettings(delay=0.1))

    await queue.flush()
    mock_executor.assert_not_called()


@pytest.mark.asyncio
async def test_action_queue_shutdown_empty(mock_executor):
    """Test that shutting down an empty queue is a no-op."""
    queue = ActionQueue(executor=mock_executor, settings=ActionQueueSettings(delay=0.1))

    await queue.shutdown()
    mock_executor.assert_not_called()


@pytest.mark.asyncio
async def test_action_queue_no_self_cancel_during_delayed_flush():
    """Test that _delayed_flush does not cancel itself via _prepare_flush.

    When _delayed_flush fires and calls _prepare_flush, the flush task is still
    the running coroutine. _prepare_flush must not cancel it, otherwise the batch
    would fail with CancelledError when the executor performs I/O.
    """
    cancel_detected = False

    async def slow_executor(actions, mode, label):
        nonlocal cancel_detected
        try:
            await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            cancel_detected = True
            raise
        return "exec-ok"

    queue = ActionQueue(
        executor=AsyncMock(side_effect=slow_executor),
        settings=ActionQueueSettings(delay=0.05),
    )

    action = Action(
        device_url="io://1234-5678-9012/1",
        commands=[Command(name=OverkizCommand.CLOSE)],
    )

    queued = await queue.add([action])
    exec_id = await queued

    assert exec_id == "exec-ok"
    assert not cancel_detected, "_delayed_flush cancelled itself via _prepare_flush"
