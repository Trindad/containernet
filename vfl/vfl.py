from time import time
import torch

from model import Model
from data import get_dataloader
from encryption import generate_keys, encrypt, decrypt, send


start = time()
# Step 1
## Initializations
LR = 1e-4 # Learning rate
SIZE_VAL = 1e4
SIZE_BATCH = 128
A, B, C = 'A', 'B', 'C'

### C
MAX_ITERS = 20
SEED = 61

# public_key, private_key = generate_keys()
losses_train = []
losses_val = []
# send_key(public_key, SEED)


### A
# SEED, key = receive()
modelA = Model()
dataloaderA = get_dataloader(A, SEED)
dataloader_valA = get_dataloader(A, SEED, train=False)
optimizerA = torch.optim.Adam(modelA.parameters(), lr=LR)

### B
# SEED, key = receive()
modelB = Model()
dataloaderB = get_dataloader(B, SEED)
dataloader_valB = get_dataloader(B, SEED, train=False)
optimizerB = torch.optim.Adam(modelB.parameters(), lr=LR)

print(f"Initialization took {time() - start:.1f}s")

### C
for i in range(MAX_ITERS):
    start_epoch = time()

    dataloaderA_iter = iter(dataloaderA)
    dataloaderB_iter = iter(dataloaderB)

    modelA.train()
    modelB.train() 

    while True:
        # Step 2

        ### A
    # for xA, _ in dataloaderA:
        try:
            xA, _ = next(dataloaderA_iter)
        except StopIteration:
            # send epoch finished to C
            break

        uA = modelA.forward(xA)
        LA = (uA**2).sum()
        
        uA_encrypted = encrypt(uA)
        LA_encrypted = encrypt(LA)
        send(B, uA_encrypted, LA_encrypted)

        ### B
    # for xB, y in dataloaderB:
        xB, y = next(dataloaderB_iter)
        uB = modelB.forward(xB)

        d_encrypted = uA_encrypted + encrypt(uB - y)
        L_encrypted = LA_encrypted + encrypt(((uB - y)**2).sum()) + encrypt((uA * (uB - y)).sum())
        send(C, L_encrypted)
        send(A, d_encrypted)


        # Step 3

        ### A
        gradientA_encrypted = d_encrypted * uA
        send(C, gradientA_encrypted)

        ### B
        gradientB_encrypted = d_encrypted * uB
        send(C, gradientB_encrypted)

        ### C
        loss = decrypt(L_encrypted) / SIZE_BATCH
        losses_train.append(loss)
        # TODO check if may stop by losses

        gradientA = decrypt(gradientA_encrypted)
        gradientB = decrypt(gradientB_encrypted)
        send(A, gradientA)
        send(B, gradientB)


        # Step 4

        ### A
        optimizerA.zero_grad()
        # https://discuss.pytorch.org/t/what-does-tensor-backward-do-mathematically/27953
        uA.backward(gradient=gradientA)
        optimizerA.step()

        ### B
        optimizerB.zero_grad()
        uB.backward(gradient=gradientB)
        optimizerB.step()

    # Validation

    ## B
    L_total = 0
    acc_total = 0

    modelA.eval()
    modelB.eval()
    for (xA, _), (xB, y) in zip(dataloader_valA, dataloader_valB):
        with torch.no_grad():
            ## A
            uA = modelA.forward(xA)
            LA = (uA**2).sum()
            LA_encrypted = encrypt(LA)
            # send LA_encrypted to B

            ## B
            uB = modelB.forward(xB)
            acc = ((uA + uB).argmax(axis=1) == y.argmax(axis=1))
            L_encrypted = LA_encrypted + encrypt(((uB - y)**2).sum()) + (uA * (uB - y)).sum()
            L_total += L_encrypted
            acc_total += acc.sum()

    # send L_total to C

    ## C
    loss = decrypt(L_total) / SIZE_VAL
    acc = acc_total / SIZE_VAL
    losses_val.append(loss)


    # TODO validation set for fuck sake
    print(f"\n\n ==== EPOCH: {i+1} ====")
    print(f"Took: {time() - start_epoch:.1f}s")
    print()
    print(f"Pred A: {uA[0]} | {uA[0].sum()}")
    print(f"Pred B: {uB[0]} | {uB[0].sum()}")
    print()
    print(f"Pred Final: {(uA[0] + uB[0]).argmax()} | {uA[0] + uB[0]} | {(uA[0] + uB[0]).sum()}")
    print(f"  Expected: {y[0].argmax()} | {y[0]}")
    print()
    print(f"Train Loss: {losses_train[-1]:.5f}")
    print(f"  Val Loss: {losses_val[-1]:.5f}")
    print(f"       Acc: {100*acc:.2f}%")

        # break
    # break
    # print(f"EPOCH: {i+1}")

print()
print(f"The whole thing took {time() - start:.1f}s")