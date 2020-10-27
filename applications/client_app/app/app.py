import requests
import re
import time

import asyncio
import websockets

websocket_ip = '10.0.0.251'

async def hello():
    uri = "ws://"+websocket_ip+":8766"
    while True:
        time.sleep(1)
        async with websockets.connect(uri) as websocket:
            name = "Client"

            await websocket.send(name)
            print(f"> {name}")

            greeting = await websocket.recv()
            print(f"< {greeting}")

asyncio.get_event_loop().run_until_complete(hello())

if __name__ == '__main__':
    start_server = websockets.serve(hello, "0.0.0.0", 8766)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

