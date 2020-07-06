import asyncio
from tahoma_api import TahomaClient
import time

username = ""
password = ""


async def main():
    client = TahomaClient(username, password)

    try:
        login = await client.login()
        devices = await client.get_devices()

        for device in devices:
            print(f"{device.label} ({device.id})")

        listener_id = await client.register_event_listener()

        while True:
            events = await client.fetch_event_listener(listener_id)
            print(events)
            time.sleep(2)

    except Exception as exception:
        print(exception)

asyncio.run(main())
