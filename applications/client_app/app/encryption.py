import numpy as np
from Pyfhel import Pyfhel, PyPtxt, PyCtxt
from pathlib import Path
from torch import Tensor
import tempfile

class HomomorphicEncryption():
    def __init__(self, pubkeyfile, ctxfile):
        self.HE = Pyfhel()
        self.HE.contextGen(p=65537, flagBatching=True)
        self.restore_public_key(pubkeyfile)
        self.restore_public_key(ctxfile)

    def has_public_key(self):
        return not self.HE.is_publicKey_empty()

    def restore_public_key(self, path):
        self.HE.restorepublicKey(path)

    def restore_context(self, path):
        self.HE.restoreContext(path)

    def encrypt_tensor(self, tensor):
        assert self.has_public_key(), "Must have a public key to encrypt"

        encrypt_vec = np.vectorize(self.HE.encryptFrac)
        return encrypt_vec(tensor.detach().cpu().numpy())

    def encode_frac(self, tensor):
        # temp_file = tempfile.NamedTemporaryFile()
        # tensor.to_file(temp_file.name)
        # with open(temp_file.name, mode='rb') as f:
        #     return f.read()
        return tensor.to_bytes()

    def encode(self, tensor):
        encode_vec =  np.vectorize(self.encode_frac)
        return encode_vec(tensor)
        # return [self.encode_frac(t) for t in tensor]

    def decode_frac(self, tensor):
        # temp_file = tempfile.NamedTemporaryFile()
        # with open(temp_file.name, mode='wb') as f:
        #     return f.write(tensor)
        # return PyCtxt(pyfhel=self.HE, fileName=temp_file.name, encoding=float)
        val = PyCtxt(pyfhel=self.HE)
        val.from_bytes(bytes(tensor), float)
        return val

    def decode(self, tensor):
        decode_vec = np.vectorize(self.decode_frac)
        return decode_vec(tensor)
        # return [self.decode_frac(t) for t in tensor]

