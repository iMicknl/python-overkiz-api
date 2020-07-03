import asyncio
from tahoma_api import TahomaClient

username = ""
password = ""

async def main():
    client = TahomaClient(username, password)
    
    try:
        login = await client.login()
        devices = await client.get_states()

        print(devices)


    except Exception as exception:
        print(exception)

asyncio.run(main())
