#!/usr/bin/env python3
# mypy: ignore-errors
# type: ignore

"""Simple example demonstrating the action queue feature."""

from __future__ import annotations

import asyncio

from pyoverkiz.auth import UsernamePasswordCredentials
from pyoverkiz.client import OverkizClient
from pyoverkiz.enums import OverkizCommand, Server
from pyoverkiz.models import Action, Command


async def example_without_queue():
    """Example: Execute actions without queue (immediate execution)."""
    print("\n=== Example 1: Without Queue (Immediate Execution) ===")

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
    print("Executing action 1...")
    # exec_id = await client.execute_action_group([action1])
    # print(f"Got exec_id immediately: {exec_id}")

    print("Without queue: Each call executes immediately as a separate API request")
    await client.close()


async def example_with_queue():
    """Example: Execute actions with queue (batched execution)."""
    print("\n=== Example 2: With Queue (Batched Execution) ===")

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
    print("Queueing action 1...")
    exec_id1 = await client.execute_action_group([action1])
    print(f"Got exec_id: {exec_id1}")

    print("Queueing action 2...")
    exec_id2 = await client.execute_action_group([action2])

    print("Queueing action 3...")
    exec_id3 = await client.execute_action_group([action3])

    print(f"Pending actions in queue: {client.get_pending_actions_count()}")

    # All three will have the same exec_id since they were batched together!
    print(f"\nExec ID 1: {exec_id1}")
    print(f"Exec ID 2: {exec_id2}")
    print(f"Exec ID 3: {exec_id3}")
    print(f"All same? {exec_id1 == exec_id2 == exec_id3}")

    print("\nWith queue: Multiple actions batched into single API request!")
    await client.close()


async def example_manual_flush():
    """Example: Manually flush the queue."""
    print("\n=== Example 3: Manual Flush ===")

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

    print("Queueing action with 10s delay...")
    # Start execution in background (don't await yet)
    exec_task = asyncio.create_task(client.execute_action_group([action]))

    # Give it a moment to queue
    await asyncio.sleep(0.1)
    print(f"Pending actions: {client.get_pending_actions_count()}")

    # Don't want to wait 10 seconds? Flush manually!
    print("Manually flushing queue...")
    await client.flush_action_queue()

    print(f"Pending actions after flush: {client.get_pending_actions_count()}")

    # Now get the result
    exec_id = await exec_task
    print(f"Got exec_id: {exec_id}")

    await client.close()


async def main():
    """Run all examples."""
    print("=" * 60)
    print("Action Queue Feature Examples")
    print("=" * 60)

    await example_without_queue()
    await example_with_queue()
    await example_manual_flush()

    print("\n" + "=" * 60)
    print("Key Benefits:")
    print("- Reduces API calls by batching actions")
    print("- Helps avoid Overkiz rate limits")
    print("- Perfect for scenes/automations with multiple devices")
    print("- Fully backward compatible (disabled by default)")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
