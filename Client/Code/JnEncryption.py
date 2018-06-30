from Encryptions.Rijndael import Rijndael
from Crypto.Cipher import Blowfish


class JnEncryption:
    def __init__(self, key, UI=None, e_type="1"):
        if e_type == 1:
            self.encryption_imp = Rijndael(key)
            self.block_size = 16
        elif e_type == 2:
            self.encryption_imp = Blowfish.new(key)
            self.block_size = 16
        else:
            raise RuntimeError

        self.UI = UI

    def encrypt(self, data):
        enc_str = ""
        total_length = len(data)
        while len(data) >= self.block_size:
            if self.UI:
                self.UI.update_progress(len(data) - self.block_size, total_length)
            enc_str += self.encryption_imp.encrypt(data[0:self.block_size])
            data = data[self.block_size:]

        if self.UI:
            self.UI.update_progress(len(data), total_length)

        if len(data) >= 1:
            enc_str += self.encryption_imp.encrypt(str('{0: <' + str(self.block_size) + '}').format(data))

        if self.UI:
            self.UI.next_page()
        return enc_str, '{0: <2}'.format(self.block_size - len(data))

    def decrypt(self, data):
        dec_str = ""
        total_length = len(data)
        while len(data) >= self.block_size:
            if self.UI:
                self.UI.update_progress(len(data) - self.block_size, total_length)
            dec_str += self.encryption_imp.decrypt(data[0:self.block_size])
            data = data[self.block_size:]
        if self.UI:
            self.UI.update_progress(len(data), total_length)
        if len(data) >= 1:
            dec_str += self.encryption_imp.decrypt(str('{0: <' + str(self.block_size) + '}').format(data))

        if self.UI:
            self.UI.next_page()
        return dec_str
