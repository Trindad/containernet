import requests
import re
import json

import asyncio
import websockets

USERS = set()
connected_users = set()

async def register(websocket):
    USERS.add(websocket)
    print(USERS)

async def unregister(websocket):
    USERS.remove(websocket)
    print(USERS)

async def broadcast(message):
    response = {"op":"BROADCAST", "value": message}
    for w in USERS:
        await w.send(json.dumps(response))

async def hello(websocket, path):
    await register(websocket)
    while True:
        try:
            async for message in websocket:
                data = json.loads(message)
                print(f"< {data}")
                if data["op"] == "IP":
                    connected_users.add(data["value"])
                    print(connected_users)
                    response = {"op":"CONIP", "value": list(connected_users)}
                    await websocket.send(json.dumps(response))
                if data["op"] == "BROADCAST":
                    await broadcast(data["value"])
        finally:
            await unregister(websocket)



print("Starting Server")
start_server = websockets.serve(hello, "0.0.0.0", 8766)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

