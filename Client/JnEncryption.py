import Rijndael


class JnEncryption:
    def __init__(self, key):
        self.encryption_imp = Rijndael(key)

    def encrypt(self, data):
        return self.encryption_imp.encrypt(data)

    def decrypt(self, data):
        return self.encryption_imp.decrypt(data)
