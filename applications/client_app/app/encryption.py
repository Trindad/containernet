import numpy as np
from Pyfhel import Pyfhel, PyPtxt, PyCtxt
from pathlib import Path
from torch import Tensor

class HomomorphicEncryption():
    def __init__(self, pubpath):
        self.HE = Pyfhel()
        self.HE.contextGen(p=65537, flagBatching=True)
        self.restore_public_key(pubpath)

    def has_public_key(self):
        return not self.HE.is_publicKey_empty()

    def restore_public_key(self, path):
        self.HE.restorepublicKey(path)

    def encrypt_tensor(self, tensor):
        assert self.has_public_key(), "Must have a public key to encrypt"

        encrypt_vec = np.vectorize(self.HE.encryptFrac)
        return encrypt_vec(tensor.detach().cpu().numpy())