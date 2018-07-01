from Encryptions.Rijndael import Rijndael
from Crypto.Cipher import Blowfish


class JnEncryption:
    """"A generic class for all the encryption implementations and future ones."""
    def __init__(self, key, e_type):
        """Sets the encryption implementation based on the type given.
        this is the only part of the code that need to be updated to add new implementations.

        :param key: The encryption key
        :param e_type: The encryption type
        """
        if e_type == 1:
            self.encryption_imp = Rijndael(key)
            self.block_size = 16
        elif e_type == 2:
            self.encryption_imp = Blowfish.new(key)
            self.block_size = 16
        else:
            raise RuntimeError

    def encrypt(self, data):
        """Encrypting the data given in blocks decided by the block size of the type.

        :param data: Data to encrypt
        :return: Encrypted data
        """
        enc_str = ""
        while len(data) >= self.block_size:
            enc_str += self.encryption_imp.encrypt(data[0:self.block_size])
            data = data[self.block_size:]

        if len(data) >= 1:
            enc_str += self.encryption_imp.encrypt(str('{0: <' + str(self.block_size) + '}').format(data))

        return enc_str, '{0: <2}'.format(self.block_size - len(data))

    def decrypt(self, data):
        """Decrypting the data given in blocks decided by the block size of the type.

        :param data: Data to decrypt
        :return: Decrypted data
        """
        dec_str = ""
        while len(data) >= self.block_size:
            dec_str += self.encryption_imp.decrypt(data[0:self.block_size])
            data = data[self.block_size:]

        if len(data) >= 1:
            dec_str += self.encryption_imp.decrypt(str('{0: <' + str(self.block_size) + '}').format(data))

        return dec_str
