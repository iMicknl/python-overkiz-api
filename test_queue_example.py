#!/usr/bin/env python3
# mypy: ignore-errors
# type: ignore

"""Simple example demonstrating the action queue feature."""

from __future__ import annotations

import asyncio
import logging

from pyoverkiz.auth import UsernamePasswordCredentials
from pyoverkiz.client import OverkizClient
from pyoverkiz.enums import OverkizCommand, Server
from pyoverkiz.models import Action, Command

_LOGGER = logging.getLogger(__name__)


async def example_without_queue():
    """Example: Execute actions without queue (immediate execution)."""
    _LOGGER.info("=== Example 1: Without Queue (Immediate Execution) ===")

    client = OverkizClient(
        server=Server.SOMFY_EUROPE,
        credentials=UsernamePasswordCredentials("user@example.com", "password"),
        action_queue_enabled=False,  # Queue disabled
    )

    # Create some example actions
    Action(
        device_url="io://1234-5678-9012/12345678",
        commands=[Command(name=OverkizCommand.CLOSE)],
    )

    # This will execute immediately
    _LOGGER.info("Executing action 1...")
    # exec_id = await client.execute_action_group([action1])
    # print(f"Got exec_id immediately: {exec_id}")

    _LOGGER.info(
        "Without queue: Each call executes immediately as a separate API request"
    )
    await client.close()


async def example_with_queue():
    """Example: Execute actions with queue (batched execution)."""
    _LOGGER.info("=== Example 2: With Queue (Batched Execution) ===")

    client = OverkizClient(
        server=Server.SOMFY_EUROPE,
        credentials=UsernamePasswordCredentials("user@example.com", "password"),
        action_queue_enabled=True,  # Queue enabled!
        action_queue_delay=0.5,  # Wait 500ms before flushing
        action_queue_max_actions=20,  # Max 20 actions per batch
    )

    # Create some example actions
    action1 = Action(
        device_url="io://1234-5678-9012/12345678",
        commands=[Command(name=OverkizCommand.CLOSE)],
    )

    action2 = Action(
        device_url="io://1234-5678-9012/87654321",
        commands=[Command(name=OverkizCommand.OPEN)],
    )

    action3 = Action(
        device_url="io://1234-5678-9012/11111111",
        commands=[Command(name=OverkizCommand.STOP)],
    )

    # These will be queued and batched together!
    _LOGGER.info("Queueing action 1...")
    exec_id1 = await client.execute_action_group([action1])
    _LOGGER.info("Got exec_id: %s", exec_id1)

    _LOGGER.info("Queueing action 2...")
    exec_id2 = await client.execute_action_group([action2])

    _LOGGER.info("Queueing action 3...")
    exec_id3 = await client.execute_action_group([action3])

    _LOGGER.info("Pending actions in queue: %s", client.get_pending_actions_count())

    # All three will have the same exec_id since they were batched together!
    _LOGGER.info("Exec ID 1: %s", exec_id1)
    _LOGGER.info("Exec ID 2: %s", exec_id2)
    _LOGGER.info("Exec ID 3: %s", exec_id3)
    _LOGGER.info("All same? %s", exec_id1 == exec_id2 == exec_id3)

    _LOGGER.info("With queue: Multiple actions batched into single API request!")
    await client.close()


async def example_manual_flush():
    """Example: Manually flush the queue."""
    _LOGGER.info("=== Example 3: Manual Flush ===")

    client = OverkizClient(
        server=Server.SOMFY_EUROPE,
        credentials=UsernamePasswordCredentials("user@example.com", "password"),
        action_queue_enabled=True,
        action_queue_delay=10.0,  # Long delay
    )

    action = Action(
        device_url="io://1234-5678-9012/12345678",
        commands=[Command(name=OverkizCommand.CLOSE)],
    )

    _LOGGER.info("Queueing action with 10s delay...")
    # Start execution in background (don't await yet)
    exec_task = asyncio.create_task(client.execute_action_group([action]))

    # Give it a moment to queue
    await asyncio.sleep(0.1)
    _LOGGER.info("Pending actions: %s", client.get_pending_actions_count())

    # Don't want to wait 10 seconds? Flush manually!
    _LOGGER.info("Manually flushing queue...")
    await client.flush_action_queue()

    _LOGGER.info("Pending actions after flush: %s", client.get_pending_actions_count())

    # Now get the result
    exec_id = await exec_task
    _LOGGER.info("Got exec_id: %s", exec_id)

    await client.close()


async def main():
    """Run all examples."""
    logging.basicConfig(level=logging.INFO)
    _LOGGER.info("=" * 60)
    _LOGGER.info("Action Queue Feature Examples")
    _LOGGER.info("=" * 60)

    await example_without_queue()
    await example_with_queue()
    await example_manual_flush()

    _LOGGER.info("%s", "=" * 60)
    _LOGGER.info("Key Benefits:")
    _LOGGER.info("- Reduces API calls by batching actions")
    _LOGGER.info("- Helps avoid Overkiz rate limits")
    _LOGGER.info("- Perfect for scenes/automations with multiple devices")
    _LOGGER.info("- Fully backward compatible (disabled by default)")
    _LOGGER.info("%s", "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
