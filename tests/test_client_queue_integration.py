"""Integration tests for OverkizClient with ActionQueue."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from pyoverkiz.client import OverkizClient
from pyoverkiz.const import SUPPORTED_SERVERS
from pyoverkiz.enums import OverkizCommand, Server
from pyoverkiz.models import Action, Command


@pytest.mark.asyncio
async def test_client_without_queue_executes_immediately():
    """Test that client without queue executes actions immediately."""
    client = OverkizClient(
        username="test@example.com",
        password="test",
        server=SUPPORTED_SERVERS[Server.SOMFY_EUROPE],
        action_queue_enabled=False,
    )

    action = Action(
        device_url="io://1234-5678-9012/1",
        commands=[Command(name=OverkizCommand.CLOSE)],
    )

    # Mock the internal execution
    with patch.object(
        client, "_OverkizClient__post", new_callable=AsyncMock
    ) as mock_post:
        mock_post.return_value = {"execId": "exec-123"}

        result = await client.execute_action_group([action])

        # Should return exec_id directly (string)
        assert isinstance(result, str)
        assert result == "exec-123"

        # Should have called API immediately
        mock_post.assert_called_once()

    await client.close()


@pytest.mark.asyncio
async def test_client_with_queue_batches_actions():
    """Test that client with queue batches multiple actions."""
    client = OverkizClient(
        username="test@example.com",
        password="test",
        server=SUPPORTED_SERVERS[Server.SOMFY_EUROPE],
        action_queue_enabled=True,
        action_queue_delay=0.1,
    )

    actions = [
        Action(
            device_url=f"io://1234-5678-9012/{i}",
            commands=[Command(name=OverkizCommand.CLOSE)],
        )
        for i in range(3)
    ]

    with patch.object(
        client, "_OverkizClient__post", new_callable=AsyncMock
    ) as mock_post:
        mock_post.return_value = {"execId": "exec-batched"}

        # Queue multiple actions quickly - start them as tasks to allow batching
        task1 = asyncio.create_task(client.execute_action_group([actions[0]]))
        task2 = asyncio.create_task(client.execute_action_group([actions[1]]))
        task3 = asyncio.create_task(client.execute_action_group([actions[2]]))

        # Give them a moment to queue
        await asyncio.sleep(0.01)

        # Should have 3 actions pending
        assert client.get_pending_actions_count() == 3

        # Wait for all to execute
        exec_id1 = await task1
        exec_id2 = await task2
        exec_id3 = await task3

        # All should have the same exec_id (batched together)
        assert exec_id1 == exec_id2 == exec_id3 == "exec-batched"

        # Should have called API only once (batched)
        mock_post.assert_called_once()

        # Check that all 3 actions were in the batch
        call_args = mock_post.call_args
        payload = call_args[0][1]  # Second argument is the payload
        assert len(payload["actions"]) == 3

    await client.close()


@pytest.mark.asyncio
async def test_client_manual_flush():
    """Test manually flushing the queue."""
    client = OverkizClient(
        username="test@example.com",
        password="test",
        server=SUPPORTED_SERVERS[Server.SOMFY_EUROPE],
        action_queue_enabled=True,
        action_queue_delay=10.0,  # Long delay
    )

    action = Action(
        device_url="io://1234-5678-9012/1",
        commands=[Command(name=OverkizCommand.CLOSE)],
    )

    with patch.object(
        client, "_OverkizClient__post", new_callable=AsyncMock
    ) as mock_post:
        mock_post.return_value = {"execId": "exec-flushed"}

        # Start execution as a task to allow checking pending count
        exec_task = asyncio.create_task(client.execute_action_group([action]))

        # Give it a moment to queue
        await asyncio.sleep(0.01)

        # Should have 1 action pending
        assert client.get_pending_actions_count() == 1

        # Manually flush
        await client.flush_action_queue()

        # Should be executed now
        assert client.get_pending_actions_count() == 0

        exec_id = await exec_task
        assert exec_id == "exec-flushed"

        mock_post.assert_called_once()

    await client.close()


@pytest.mark.asyncio
async def test_client_close_flushes_queue():
    """Test that closing the client flushes pending actions."""
    client = OverkizClient(
        username="test@example.com",
        password="test",
        server=SUPPORTED_SERVERS[Server.SOMFY_EUROPE],
        action_queue_enabled=True,
        action_queue_delay=10.0,
    )

    action = Action(
        device_url="io://1234-5678-9012/1",
        commands=[Command(name=OverkizCommand.CLOSE)],
    )

    with patch.object(
        client, "_OverkizClient__post", new_callable=AsyncMock
    ) as mock_post:
        mock_post.return_value = {"execId": "exec-closed"}

        # Start execution as a task
        exec_task = asyncio.create_task(client.execute_action_group([action]))

        # Give it a moment to queue
        await asyncio.sleep(0.01)

        # Close should flush
        await client.close()

        # Should be executed
        exec_id = await exec_task
        assert exec_id == "exec-closed"

        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_client_queue_respects_max_actions():
    """Test that queue flushes when max actions is reached."""
    client = OverkizClient(
        username="test@example.com",
        password="test",
        server=SUPPORTED_SERVERS[Server.SOMFY_EUROPE],
        action_queue_enabled=True,
        action_queue_delay=10.0,
        action_queue_max_actions=2,  # Max 2 actions
    )

    actions = [
        Action(
            device_url=f"io://1234-5678-9012/{i}",
            commands=[Command(name=OverkizCommand.CLOSE)],
        )
        for i in range(3)
    ]

    with patch.object(
        client, "_OverkizClient__post", new_callable=AsyncMock
    ) as mock_post:
        mock_post.return_value = {"execId": "exec-123"}

        # Add 2 actions as tasks to trigger flush
        task1 = asyncio.create_task(client.execute_action_group([actions[0]]))
        task2 = asyncio.create_task(client.execute_action_group([actions[1]]))

        # Wait a bit for flush
        await asyncio.sleep(0.05)

        # First 2 should be done
        exec_id1 = await task1
        exec_id2 = await task2
        assert exec_id1 == "exec-123"
        assert exec_id2 == "exec-123"

        # Add third action - starts new batch
        exec_id3 = await client.execute_action_group([actions[2]])

        # Should have exec_id directly (waited for batch to complete)
        assert exec_id3 == "exec-123"

        # Should have been called twice (2 batches)
        assert mock_post.call_count == 2

    await client.close()
