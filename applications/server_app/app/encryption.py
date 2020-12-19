import numpy as np
from Pyfhel import Pyfhel, PyPtxt, PyCtxt
from pathlib import Path
from torch import Tensor

class HomomorphicEncryption():
    def __init__(self, client=False):
        self.client = client

        self.HE = Pyfhel()
        self.HE.contextGen(p=65537, flagBatching=True)

        self.HE.keyGen()
        Path("./encryption").mkdir(parents=True, exist_ok=True)
        self.HE.savepublicKey("./encryption/pub.key")

    def export_public_key_contents(self):
        with open('./encryption/pub.key', mode='rb') as f:
            return f.read()

    def has_public_key(self):
        return not self.HE.is_publicKey_empty()

    def encrypt_tensor(self, tensor):
        assert self.has_public_key(), "Must have a public key to encrypt"

        encrypt_vec = np.vectorize(self.HE.encryptFrac)
        return encrypt_vec(tensor.detach().cpu().numpy())

    def decrypt_tensor(self, tensor):
        assert not self.client, "Clients are not able to decrypt"

        decrypt_vec = np.vectorize(self.HE.decryptFrac)
        return Tensor(decrypt_vec(tensor))
