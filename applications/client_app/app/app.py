import requests
import re
import time
import socket
import json

import asyncio
import websockets

websocket_ip = '10.0.0.251'
# websocket_ip = 'localhost'

print("Starting service")

async def loop(websocket):
    while True:
        time.sleep(1)

        local_ip = socket.gethostbyname(socket.gethostname())

        messsage = {"op":"IP", "value":local_ip}
        await websocket.send(json.dumps(messsage))
        print(f"> {local_ip}")

        resp = await websocket.recv()
        print(f"< {resp}")

        messsage = {"op":"BROADCAST", "value":"hello from " + local_ip}
        await websocket.send(json.dumps(messsage))

        resp = await websocket.recv()
        print(f"< {resp}")

async def hello():
    uri = "ws://"+websocket_ip+":8766"
    
    while True:
        async with websockets.connect(uri) as websocket:
            await loop(websocket)


asyncio.get_event_loop().run_until_complete(hello())

