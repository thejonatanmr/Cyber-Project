import json
import socket
import ssl
import struct
import Queue
import hashlib
from base64 import *
from JnEncryption import JnEncryption
import ConfigParser

"""Reads id and version from config and sets the config variable for future use."""
CONFIG = ConfigParser.RawConfigParser()
CONFIG.read('config.cfg')
PROGRAM_ID = struct.pack("i", 1111)
PROGRAM_V = struct.pack("i", CONFIG.getint("Config", "version"))


class ClientSide:
    def __init__(self, UI):
        """"Reads IP and PORT from config abd sets initial variables"""
        global CONFIG
        self.server = CONFIG.get("Config", "ip")
        self.port = CONFIG.getint("Config", "port")
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ssl_socket = None
        self.session = ""
        self.operation_queue = Queue.Queue()
        self.UI = UI

    def run(self):
        """Opens a socket and tries to connect to the server.
        Require a certificate from the server. We used a self-signed certificate
        so here ca_certs must be the server certificate itself.
        :return: true of successful connection and false on a failed one.
        """

        self.ssl_socket = ssl_sock = ssl.wrap_socket(self.client_socket, ca_certs="server.crt",
                                                     cert_reqs=ssl.CERT_REQUIRED)
        try:
            ssl_sock.connect((self.server, self.port))
            return True

        except Exception:
            self.UI.raise_error_box("Server error", "Could not connect to the server, please try again")
            return False

    def check_enc_file(self, file_path):
        """Verifies the program version and id on a file.
        :return: true if the file is encrypted by this program with its current version and false otherwise.
        """
        global PROGRAM_V, PROGRAM_ID
        with open(file_path, "rb") as my_file:
            data = my_file.read(8)
        ID = data[0:4]
        V = data[4:8]

        if struct.unpack("i", V) == struct.unpack("i", PROGRAM_V) and struct.unpack("i", ID) == struct.unpack("i",
                                                                                                              PROGRAM_ID):
            return True
        else:
            return False

    def new_user(self, user, password):
        """Sends the server the "new-user" operation in order to register in the server with the given password and username
        :return: True on successful registration and false otherwise.
        """
        self.ssl_socket.write(json.dumps({"op": "new-user", "data": {"user": user, "password": password}}))

        json_data = self.ssl_socket.read()
        data = json.loads(json_data)
        if data["op"] == "ok":
            return True
        else:
            self.UI.raise_error_box("error", data["data"]["error"])
            return False

    def login(self, user, password):
        """Sends the server the "login" operation in order to login in the server with the given password and username
        :return: True on successful login and false otherwise.
        """
        self.ssl_socket.write(json.dumps({"op": "login", "data": {"user": user, "password": password}}))
        json_data = self.ssl_socket.read()
        try:
            data = json.loads(json_data)
            if data["op"] == "ok":
                self.session = data["data"]["session id"]
                return True
            else:
                self.UI.raise_error_box("error", data["data"]["error"])
                return False

        except Exception:
            self.UI.raise_error_box("Server Error", "Error reading data sent from server.")

    def encrypt(self, e_file, e_type):
        """Reading and encrypting a given file. using the chosen encryption type and by getting a new key from the server
        opens a new file with the same name as the old file but with '.jn' added at the end and saves the encrypted data
        there.

        :param e_file: the file path
        :param e_type: the type of encryption
        """
        global PROGRAM_ID, PROGRAM_V
        type_id = CONFIG.getint("Encryptions", e_type)
        self.ssl_socket.write(json.dumps({"op": "new-key", "data": {"e_type": type_id, "session": self.session}}))

        json_data = self.ssl_socket.read()
        data = json.loads(json_data)
        if data["op"] == "key":
            curr_key = data["data"]["key"]

            try:
                enc = JnEncryption(curr_key, type_id)

            except RuntimeError:
                self.UI.raise_error_box("error", "Unknown encryption type", move_frame=True, frame='EncDecPage')
                return False

            with open(e_file, "rb") as my_file:
                data = my_file.read()

            encrypted_data, added_length = enc.encrypt(data)

            start_seg = encrypted_data[0:10]
            unfinished_encrypted_data = encrypted_data[10:]

            headed_encrypted_data = PROGRAM_ID + PROGRAM_V + unfinished_encrypted_data
            md = hashlib.md5()
            md.update(headed_encrypted_data)
            key_id = md.hexdigest()

            b64_start = b64encode(start_seg)

            while True:
                try:
                    self.ssl_socket.write(
                        json.dumps({"op": "set-hash",
                                    "data": {"key-id": key_id, "start_seg": b64_start,
                                             "e_type": type_id, "session": self.session}}))
                except RuntimeError:
                    self.UI.raise_error_box("error", "Unknown encryption type", move_frame=True, frame='EncDecPage')
                    return False

                json_data = self.ssl_socket.read()
                data = json.loads(json_data)
                if data["op"] == "ok":
                    with open(e_file + ".jn", "wb") as my_file:
                        my_file.write(headed_encrypted_data + added_length)
                    return True
        else:
            if "error" in data["data"]:
                self.UI.raise_error_box("error", data["data"]["error"], move_frame=True, frame='EncDecPage')
                return False
            else:
                self.UI.raise_error_box("error", "Unknown error", move_frame=True, frame='EncDecPage')
                return False

    def decrypt(self, d_file):
        """Reading and decrypting a given file. the decryption type and the key is given by the server.
        the decrypted data will be saved in the same file path with the same name but without the '.jn' at the end.
        the decryption only works on file encrypted by this program with its current version.

        :param d_file: the file path
        """
        global PROGRAM_ID, PROGRAM_V

        if d_file[-3:] != ".jn":
            self.UI.raise_error_box("File error", "The file type is not '.jn'. can not decrypt this file", move_frame=True, frame='EncDecPage')
            return False

        with open(d_file, "rb") as encrypted_file:
            headed_encrypted_data = encrypted_file.read()

        added_length = headed_encrypted_data[-2:]
        headed_encrypted_data = headed_encrypted_data[0:-2]

        md = hashlib.md5()
        md.update(headed_encrypted_data)
        key_id = md.hexdigest()

        self.ssl_socket.write(json.dumps({"op": "get-key", "data": {"key-id": key_id, "session": self.session}}))
        json_data = self.ssl_socket.read()
        data = json.loads(json_data)
        if data["op"] == "key":
            key = data["data"]["key"]
            coded_start = data["data"]["start_seg"]
            start_seg = b64decode(coded_start)

            try:
                dec = JnEncryption(key, data["data"]["e_type"])

            except RuntimeError:
                self.UI.raise_error_box("error", "Unknown encryption type", move_frame=True, frame='FilePage')
                return False

            ID = headed_encrypted_data[0:4]
            V = headed_encrypted_data[4:8]

            if struct.unpack("i", ID) == struct.unpack("i", PROGRAM_ID) and struct.unpack("i", V) == struct.unpack("i",
                                                                                                                   PROGRAM_V):
                unfinished_encrypted_data = headed_encrypted_data[8:]
                encrypted_data = start_seg + unfinished_encrypted_data

                data = dec.decrypt(encrypted_data)

                if int(added_length) != 0:
                    data = data[0:-int(added_length)]

                with open(d_file[:-3], "wb") as final_file:
                    final_file.write(data)

                while True:
                    self.ssl_socket.write(
                        json.dumps({"op": "del-key", "data": {"key-id": key_id, "session": self.session}}))

                    json_data = self.ssl_socket.read()
                    data = json.loads(json_data)
                    if data["op"] == "ok":
                        return True
            else:
                self.UI.raise_error_box("File error", "Could not detect the file as an encrypted file", move_frame=True,
                                        frame="FilePage")
                return False


        else:
            if "error" in data["data"]:
                self.UI.raise_error_box("error", data["data"]["error"], move_frame=True, frame='FilePage')
                return False
            else:
                self.UI.raise_error_box("error", "Unknown error", move_frame=True, frame='FilePage')
                return False

    def exit(self):
        """closing the communication with the server and the socket."""
        self.ssl_socket.write(json.dumps({"op": "close", "data": {"session": self.session}}))
        self.client_socket.close()
