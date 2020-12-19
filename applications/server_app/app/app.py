import requests
import re
import json

import jsonpickle

import asyncio
import websockets

import time

from threading import Thread, Lock

from encryption import HomomorphicEncryption

import operations as op

import logging

logger = logging.getLogger('websockets')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

MAX_ITERS = 100
SEED = 61
LR = 1e-4  # Learning rate
BATCH_SIZE = 128

encrypter = HomomorphicEncryption()

losses = []

# Global variables
PRIMARY_CLIENT = None
SECONDARY_CLIENT = None
CLIENTS = set()
connected_users = set()

# mutex sync variables
RESPONSE = asyncio.Queue()


async def register(websocket):
    CLIENTS.add(websocket)
    print(CLIENTS)


async def unregister(websocket):
    CLIENTS.remove(websocket)
    print(CLIENTS)


async def sendParams(websocket, request):
    print("request to send params received")
    primary = request["value"]
    global PRIMARY_CLIENT
    global SECONDARY_CLIENT
    if primary:
        print("Primary client connected")
        PRIMARY_CLIENT = websocket
    else:
        print("Secondary client connected")
        SECONDARY_CLIENT = websocket

    params = {"seed": SEED, "lr": LR, "batch_size": BATCH_SIZE, "pub": jsonpickle.encode(encrypter.export_public_key_contents())}
    response = {"op": "PARAMS", "value": params}
    print("Sending params to client")
    await websocket.send(json.dumps(response))


async def broadcast(message):
    response = {"op": "BROADCAST", "value": message}
    for w in CLIENTS:
        await w.send(json.dumps(response))


async def server(websocket, path):
    print("New client")
    await register(websocket)
    while True:
        try:
            async for message in websocket:
                request = json.loads(message)
                print(f"Request received from client {request['op']}")
                if request["op"] == op.SEND_PARAMS:
                    await sendParams(websocket, request)
                else:
                    global RESPONSE
                    await RESPONSE.put(request)

        finally:
            print("Unregistering client")
            await unregister(websocket)


async def calculate_step():
    request = {"op": op.SECONDARY_STEP}
    await SECONDARY_CLIENT.send(json.dumps(request))
    print("secondary step request sent")

    print("Awaiting for step response")
    response = await RESPONSE.get()
    print("Step response received")

    epoch_end = response['value']['epoch_end']
    if not epoch_end:
        u = response['value']['u']
        L = response['value']['L']
        value = {"u": u, "L": L}
        request = {"op": op.PRIMARY_STEP, "value": value}
        await PRIMARY_CLIENT.send(json.dumps(request))
        print("Awaiting for step response")
        response = await RESPONSE.get()
        print("Awaiting for step response")

        L_encrypted = response['value']['L']
        gradient = response['value']['d']

        L_encrypted = jsonpickle.decode(L_encrypted)

        loss = encrypter.decrypt_tensor(L_encrypted) / BATCH_SIZE
        losses.append(loss)
        print("***********")
        print("LOSS:", loss)
        print("***********")

        request = {"op": op.BACKPROP, "value": gradient} 
        await SECONDARY_CLIENT.send(json.dumps(request))
        await PRIMARY_CLIENT.send(json.dumps(request))

        response = await RESPONSE.get() # wait for both responses
        response = await RESPONSE.get() 
    return epoch_end

async def init_epoch():
    request = {"op": op.INIT_EPOCH}
    await PRIMARY_CLIENT.send(json.dumps(request))
    await SECONDARY_CLIENT.send(json.dumps(request))
    await RESPONSE.get() # await for confirmations
    await RESPONSE.get()

async def controller():
    epoch = 0
    MAX_EPOCHS = 10
    while epoch < MAX_EPOCHS:
        if PRIMARY_CLIENT == None or SECONDARY_CLIENT == None:
            await asyncio.sleep(1)
            print("Not all clients are connected yet")
            continue

        # EPOCH
        print(f"EPOCH: {epoch} starting")
        await init_epoch()
        epoch_end = False
        while not epoch_end:
            epoch_end = await calculate_step()
            print("step done")
        print(f"EPOCH: {epoch} done")
        print(f"EPOCH: loss {losses[-1]}")
        print("*******************************")
        epoch += 1



async def main():
    start_server = websockets.serve(server, "0.0.0.0", 8766, ping_interval=None)

    print("Starting Server")
    await asyncio.wait([start_server, controller()], return_when=asyncio.ALL_COMPLETED)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
