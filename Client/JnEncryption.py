from Rijndael import Rijndael


class JnEncryption:
    def __init__(self, key):
        self.encryption_imp = Rijndael(key)

    def encrypt(self, data):
        enc_str = ""
        while len(data) >= 16:
            enc_str += self.encryption_imp.encrypt(data[0:16])
            data = data[16:]

        if len(data) >= 1:
            enc_str += self.encryption_imp.encrypt('{0: <16}'.format(data))
        return enc_str

    def decrypt(self, data):
        dec_str = ""
        while len(data) >= 16:
            dec_str += self.encryption_imp.decrypt(data[0:16])
            data = data[16:]

        if len(data) >= 1:
            dec_str += self.encryption_imp.decrypt('{0: <16}'.format(data))
        return dec_str
