import numpy as np
from Pyfhel import Pyfhel, PyPtxt, PyCtxt
from pathlib import Path
from torch import Tensor
import tempfile
import base64

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
        temp_file = tempfile.NamedTemporaryFile()
        # tensor.to_file(temp_file.name)
        with open(temp_file.name, mode="w+b") as f:
            tensor.save(temp_file.name)
            bc = f.read()
            b64 = str(base64.b64encode(bc))[2:-1]
            return b64
        # return tensor.to_bytes()

    def encode(self, tensor):
        print("Encoding message")
        encode_vec =  np.vectorize(self.encode_frac)
        res = encode_vec(tensor)
        print("Message encoded")
        return res
        # return tensor
        # return [self.encode_frac(t) for t in tensor]

    def decode_frac(self, b64):
        temp_file = tempfile.NamedTemporaryFile()
        with open(temp_file.name, mode='w+b') as f:
            x = bytes(b64, encoding='utf-8')
            x = base64.decodebytes(x)
            f.write(x)
            c = self.HE.encryptFrac(0)
            c.load(temp_file.name, "float")
            return c

        c = self.HE.encryptFrac(0)
        c.load(temp_file.name, "float")
        return c
        # val = PyCtxt(pyfhel=self.HE)
        # val.from_bytes(bytes(tensor), float)
        # return val

    def decode(self, tensor):
        print("Decoding message")
        decode_vec = np.vectorize(self.decode_frac)
        res = decode_vec(tensor)
        print("Message decoded")
        return res
        # return tensor
        # return [self.decode_frac(t) for t in tensor]


