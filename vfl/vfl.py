import torch

from model import Model
from data import get_dataloader
from encryption import generate_keys, encrypt, decrypt, send


# Step 1
## Initializations
LR = 1e-4 # Learning rate
A, B, C = 'A', 'B', 'C'

### C
MAX_ITERS = 10
SEED = 61

# public_key, private_key = generate_keys()
losses = []
# send_key(public_key, SEED)


### A
# SEED, key = receive()
modelA = Model()
dataloaderA = get_dataloader(A, SEED)
optimizerA = torch.optim.Adam(modelA.parameters(), lr=LR)

### B
# SEED, key = receive()
modelB = Model()
dataloaderB = get_dataloader(B, SEED)
optimizerB = torch.optim.Adam(modelB.parameters(), lr=LR)


### C
for i in range(MAX_ITERS):
    finished_epoch = False

    dataloaderA_iter = iter(dataloaderA)
    dataloaderB_iter = iter(dataloaderB)

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
        gradientA_encrypted = d_encrypted #* xA
        send(C, gradientA_encrypted)

        ### B
        gradientB_encrypted = d_encrypted #* xB
        send(C, gradientB_encrypted)

        ### C
        loss = decrypt(L_encrypted) / 128
        losses.append(loss)
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



    print(f"\n\n ==== EPOCH: {i} ====")
    print(f"Prediction A: {uA[0]}")
    print(f"Prediction B: {uB[0]}")

    print(f"Prediction B: {uA[0] + uB[0]} - {(uA[0] + uB[0]).argmax()}")
    print(f"Expected: {y[0]} - {y[0].argmax()}")
    print(f"Loss: {loss:.5f}")
        # break
    # break
    # print(f"EPOCH: {i}")


