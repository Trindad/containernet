import requests
import re
import time
import socket
import json
import torch
import sys
import jsonpickle

import asyncio
import websockets

import operations as op
from data import get_dataloader
from model import Model
from encryption import generate_keys, encrypt, decrypt, send

if len(sys.argv) != 3:
    print(f"invalid arguments {sys.argv}, usage: [indentifier] [primary]")
    quit()

INDENTIFIER = sys.argv[1]
PRIMARY = sys.argv[2] == "true"

# websocket_ip = '10.0.0.251'
websocket_ip = 'localhost'
dataloader = None
identifier = ""

SEED = 0
LR = 0

print("Starting service")


async def fetchParams(websocket):
    messsage = {"op": op.SEND_PARAMS, "value": PRIMARY}
    await websocket.send(json.dumps(messsage))
    response = await websocket.recv()

    message = json.loads(response)

    print(f"Params received: {message}")

    global SEED
    global LR
    SEED = message["value"]["seed"]
    LR = message["value"]["lr"]


async def step_secondary(model, dataloader_iter, websocket):
    print("starting secondary step")
    message = {"op": op.SECONDARY_STEP}

    try:
        X, _ = next(dataloader_iter)
    except StopIteration:
        print("stop iteration exception")
        result = {"epoch_end": True}
        message["value"] = result
        await websocket.send(json.dumps(message))
        return
        # send epoch finished to C
        # break

    print("Calculating secondary step")
    u = model.forward(X)
    L = (u**2).sum()

    u_encrypted = encrypt(u)
    L_encrypted = encrypt(L)

    u_serialized = jsonpickle.encode(u_encrypted)
    L_serialized = jsonpickle.encode(L_encrypted)

    result = {"u": u_serialized, "L": L_serialized, "epoch_end": False}
    message["value"] = result

    print("Sending results")
    await websocket.send(json.dumps(message))
    print("Results sent")

    return u


async def step_primary(model,  u_secondary, L_secondary, dataloader_iter, websocket):
    print("primary step")
    X, Y = next(dataloader_iter)
    u = model.forward(X)

    u_secondary = jsonpickle.decode(u_secondary)
    L_secondary = jsonpickle.decode(L_secondary)

    d_encrypted = u_secondary + encrypt(u - Y)
    L_encrypted = L_secondary + \
        encrypt(((u - Y)**2).sum()) + encrypt((u_secondary * (u - Y)).sum())

    d_serialized = jsonpickle.encode(d_encrypted)
    L_serialized = jsonpickle.encode(L_encrypted)

    message = {"op": op.PRIMARY_STEP}

    result = {"d": d_serialized, "L": L_serialized, "epoch_end": False}
    message["value"] = result

    print("Sending results")
    await websocket.send(json.dumps(message))
    print("Results sent")

    return u


async def backprop(u, gradient, optimizer, websocket):
    gradient = jsonpickle.decode(gradient)

    optimizer.zero_grad()
    # https://discuss.pytorch.org/t/what-does-tensor-backward-do-mathematically/27953
    u.backward(gradient=gradient)
    optimizer.step()

    message = {"op": op.BACKPROP}
    await websocket.send(json.dumps(message))

    return u


async def loop(websocket):
    await fetchParams(websocket)

    model = Model()
    dataloader = get_dataloader(INDENTIFIER, SEED)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)

    u = None

    dataloader_iter = iter(dataloader)
    while True:  # epoch
        async for message in websocket:
            request = json.loads(message)
            print("request received", request["op"])
            if request["op"] == op.INIT_EPOCH:
                dataloader_iter = iter(dataloader)  # reset the dataloader
                message = {"op": op.INIT_EPOCH}
                await websocket.send(json.dumps(message))
            if request["op"] == op.SECONDARY_STEP:
                u = await step_secondary(model, dataloader_iter, websocket)
            elif request["op"] == op.PRIMARY_STEP:
                u = await step_primary(model, request["value"]["u"], request["value"]["L"], dataloader_iter, websocket)
            elif request["op"] == op.BACKPROP:
                gradient = request['value']
                u = await backprop(u, gradient, optimizer, websocket)


async def client():
    uri = "ws://"+websocket_ip+":8766"

    while True:
        async with websockets.connect(uri) as websocket:
            await loop(websocket)


asyncio.get_event_loop().run_until_complete(client())
