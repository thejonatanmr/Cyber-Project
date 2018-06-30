from Encryptions.Rijndael import Rijndael


class JnEncryption:
    def __init__(self, key, UI=None):
        self.encryption_imp = Rijndael(key)
        self.UI = UI

    def encrypt(self, data):
        enc_str = ""
        total_length = len(data)
        while len(data) >= 16:
            if self.UI:
                self.UI.update_progress(len(data) - 16, total_length)
            enc_str += self.encryption_imp.encrypt(data[0:16])
            data = data[16:]

        if self.UI:
            self.UI.update_progress(len(data), total_length)

        if len(data) >= 1:
            enc_str += self.encryption_imp.encrypt('{0: <16}'.format(data))

        if self.UI:
            self.UI.next_page()
        return enc_str, '{0: <2}'.format(16-len(data))

    def decrypt(self, data):
        dec_str = ""
        total_length = len(data)
        while len(data) >= 16:
            if self.UI:
                self.UI.update_progress(len(data) - 16, total_length)
            dec_str += self.encryption_imp.decrypt(data[0:16])
            data = data[16:]
        if self.UI:
            self.UI.update_progress(len(data), total_length)
        if len(data) >= 1:
            dec_str += self.encryption_imp.decrypt('{0: <16}'.format(data))

        if self.UI:
            self.UI.next_page()
        return dec_str
