from time import time
import torch

from model import Model
from data import get_dataloader
from encryption import HomomorphicEncryption, generate_keys, encrypt, decrypt, send


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
encrypterC = HomomorphicEncryption()

losses_train = []
losses_val = []
# send_key(public_key, SEED)


### A
# SEED, key = receive()
modelA = Model()
dataloaderA = get_dataloader(A, SEED)
dataloader_valA = get_dataloader(A, SEED, train=False)
optimizerA = torch.optim.Adam(modelA.parameters(), lr=LR)
encrypterA = HomomorphicEncryption(client=True)

### B
# SEED, key = receive()
modelB = Model()
dataloaderB = get_dataloader(B, SEED)
dataloader_valB = get_dataloader(B, SEED, train=False)
optimizerB = torch.optim.Adam(modelB.parameters(), lr=LR)
encrypterB = HomomorphicEncryption(client=True)

print(f"Initialization took {time() - start:.1f}s")

### C
for i in range(MAX_ITERS):
    start_epoch = time()

    dataloaderA_iter = iter(dataloaderA)
    dataloaderB_iter = iter(dataloaderB)

    modelA.train()
    modelB.train() 

    while True:
        print('.', end='', flush=True)
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
        
        uA_encrypted = encrypterA.encrypt_tensor(uA)
        LA_encrypted = encrypterA.encrypt_tensor(LA)
        send(B, uA_encrypted, LA_encrypted)

        ### B
    # for xB, y in dataloaderB:
        xB, y = next(dataloaderB_iter)
        uB = modelB.forward(xB)

        d_encrypted = uA_encrypted + encrypterB.encrypt_tensor(uB - y)
        L_encrypted = LA_encrypted + encrypterB.encrypt_tensor(((uB - y)**2).sum()) + (((uA_encrypted * (uB - y).detach().cpu().numpy()).sum()) * 2)
        send(C, L_encrypted)
        send(A, d_encrypted)


        # Step 3
        ### C
        loss = encrypterC.decrypt_tensor(L_encrypted) / SIZE_BATCH
        losses_train.append(loss)
        # TODO check if may stop by losses

        gradient = encrypterC.decrypt_tensor(d_encrypted)
        send(A, gradient)
        send(B, gradient)


        # Step 4

        ### A
        optimizerA.zero_grad()
        # https://discuss.pytorch.org/t/what-does-tensor-backward-do-mathematically/27953
        uA.backward(gradient=gradient)
        optimizerA.step()

        ### B
        optimizerB.zero_grad()
        uB.backward(gradient=gradient)
        optimizerB.step()

    print()
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
            uA_encrypted = encrypt(uA)
            LA_encrypted = encrypt(LA)
            # send LA_encrypted, uA_encrypted to B

            ## B
            uB = modelB.forward(xB)
            u_encrypted = uA_encrypted + encrypt(uB)
            L_encrypted = LA_encrypted + encrypt(((uB - y)**2).sum()) + ((uA_encrypted * (uB - y)).sum() * 2)

            ## C
            u = u_encrypted.argmax(axis=1)
            
            ## B
            acc = u == y.argmax(axis=1)

            
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