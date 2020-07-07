import asyncio
import time

from tahoma_api.client import TahomaClient

# TODO use .env file
USERNAME = ""
PASSWORD = ""


async def main() -> None:
    client = TahomaClient(USERNAME, PASSWORD)

    await client.login()
    devices = await client.get_devices()

    for device in devices:
        print(f"{device.label} ({device.id})")

    listener_id = await client.register_event_listener()

    while True:
        events = await client.fetch_event_listener(listener_id)
        print(events)
        time.sleep(2)


asyncio.run(main())
