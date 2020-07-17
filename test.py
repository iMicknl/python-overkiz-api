import asyncio
import time

from tahoma_api.client import TahomaClient

# TODO use .env file
USERNAME = ""
PASSWORD = ""


async def main() -> None:
    client = TahomaClient(USERNAME, PASSWORD)

    try:
        await client.login()
    except Exception as exception:  # pylint: disable=broad-except
        print(exception)
        return await client.close()

    devices = await client.get_devices()

    for device in devices:
        print(f"{device.label} ({device.id}) - {device.controllable_name}")
        print(f"{device.widget} - {device.ui_class}")
        # print(device.states)
        # print(device.definition)

    # Create an event listener and poll it
    listener_id = await client.register_event_listener()

    while True:
        events = await client.fetch_event_listener(listener_id)
        print(events)

        time.sleep(2)

    # Make sure you call client.close() when you are done
    await client.close()


asyncio.run(main())
