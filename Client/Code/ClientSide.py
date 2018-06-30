import json
import socket
import ssl
import struct
import Queue
import hashlib
from base64 import *
from JnEncryption import JnEncryption
import ConfigParser

CONFIG = ConfigParser.RawConfigParser()
CONFIG.read('config.cfg')
PROGRAM_ID = struct.pack("i", 1111)
PROGRAM_V = struct.pack("i", CONFIG.getint("Config", "version"))


class ClientSide:
    def __init__(self, UI):
        global CONFIG
        self.server = CONFIG.get("Config", "ip")
        self.port = CONFIG.getint("Config", "port")
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ssl_socket = None
        self.session = ""
        self.operation_queue = Queue.Queue()
        self.UI = UI

    def run(self):
        # Require a certificate from the server. We used a self-signed certificate
        # so here ca_certs must be the server certificate itself.
        self.ssl_socket = ssl_sock = ssl.wrap_socket(self.client_socket, ca_certs="server.crt",
                                                     cert_reqs=ssl.CERT_REQUIRED)
        try:
            ssl_sock.connect((self.server, self.port))

        except Exception:
            print "error connecting to the server"
            self.UI.raise_error_box("Server error", "Could not connect to the server, please try again")

    def check_enc_file(self, file_path):
        global PROGRAM_V, PROGRAM_ID
        with open(file_path, "rb") as my_file:
            data = my_file.readline()
        ID = data[0:4]
        V = data[4:8]

        if struct.unpack("i", V) == struct.unpack("i", PROGRAM_V) and struct.unpack("i", ID) == struct.unpack("i",
                                                                                                              PROGRAM_ID):
            return True
        else:
            return False

    def new_user(self, user, password):
        self.ssl_socket.write(json.dumps({"op": "new-user", "data": {"user": user, "password": password}}))

        json_data = self.ssl_socket.read()
        data = json.loads(json_data)
        if data["op"] == "ok":
            return True
        else:
            self.UI.raise_error_box("error", data["data"]["error"])
            return False

    def login(self, user, password):
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

    def encrypt(self, e_file):
        global PROGRAM_ID, PROGRAM_V
        self.ssl_socket.write(json.dumps({"op": "new-key", "data": {"session": self.session}}))

        json_data = self.ssl_socket.read()
        data = json.loads(json_data)
        if data["op"] == "key":
            curr_key = data["data"]["key"]
            enc = JnEncryption(curr_key, self.UI.frames["WorkingPage"])

            with open(e_file, "rb") as my_file:
                data = my_file.read()

            encrypted_data, added_length = enc.encrypt(data)

            # TODO fix
            start_seg = encrypted_data[0:10]
            unfinished_encrypted_data = encrypted_data[10:]

            headed_encrypted_data = PROGRAM_ID + PROGRAM_V + unfinished_encrypted_data
            md = hashlib.md5()
            md.update(headed_encrypted_data)
            key_id = md.hexdigest()

            b64_start = b64encode(start_seg)

            while True:
                self.ssl_socket.write(
                    json.dumps({"op": "set-hash",
                                "data": {"key-id": key_id, "start_seg": b64_start, "session": self.session}}))
                json_data = self.ssl_socket.read()
                data = json.loads(json_data)
                if data["op"] == "ok":
                    with open(e_file + ".jn", "wb") as my_file:
                        my_file.write(headed_encrypted_data + added_length)
                    break
        else:
            if "error" in data["data"]:
                self.UI.raise_error_box("error", data["data"]["error"], move_frame=True, frame='FinishPage')
            else:
                self.UI.raise_error_box("error", "Unknown error", move_frame=True, frame='FinishPage')

    def decrypt(self, d_file):
        global PROGRAM_ID, PROGRAM_V
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
            dec = JnEncryption(key, self.UI.frames["WorkingPage"])

            ID = headed_encrypted_data[0:4]
            V = headed_encrypted_data[4:8]

            if struct.unpack("i", ID) == struct.unpack("i", PROGRAM_ID) and struct.unpack("i", V) == struct.unpack("i",
                                                                                                                   PROGRAM_V):
                unfinished_encrypted_data = headed_encrypted_data[8:]
                encrypted_data = start_seg + unfinished_encrypted_data

                with open("after_enc.txt", "wb") as my_file:
                    my_file.write(encrypted_data)

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
                        break
            else:
                self.UI.raise_error_box("File error", "Could not detect the file as an encrypted file", move_frame=True,
                                        frame="FinishPage")


        else:
            if "error" in data["data"]:
                self.UI.raise_error_box("error", data["data"]["error"], move_frame=True, frame='FinishPage')
            else:
                self.UI.raise_error_box("error", "Unknown error", move_frame=True, frame='FinishPage')

    def exit(self):
        self.ssl_socket.write(json.dumps({"op": "close", "data": {"session": self.session}}))
        self.client_socket.close()