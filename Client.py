import json
import socket
import ssl
import queue
import threading
import hashlib


class Client:
    def __init__(self, server="localhost", port=3075):
        self.server = server
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ssl_socket = None
        self.operations = queue.Queue(maxsize=1)
        self.user = ""
        self.password = ""
        self.session = ""

    def run(self):
        # Require a certificate from the server. We used a self-signed certificate
        # so here ca_certs must be the server certificate itself.
        self.ssl_socket = ssl_sock = ssl.wrap_socket(self.client_socket, ca_certs="keys/server.crt",
                                                     cert_reqs=ssl.CERT_REQUIRED)
        try:
            ssl_sock.connect((self.server, self.port))
            # threading.Thread(target=self.input_thread).start()
            threading.Thread(target=self.server_thread).start()
        except:
            print "error connecting to the server"
            return False

    # def input_thread(self):
    #     input = raw_input()
    #     self.operations.put(self.format_input(input))

    def server_thread(self):
        while True:
            input = raw_input()
            self.operations.put(self.format_input(input))
            if self.operations.qsize() >= 1:
                operation = self.operations.get()
                formatted_operation = json.loads(operation)
                if formatted_operation["op"] == "new-user":
                    self.new_user(formatted_operation["user"], formatted_operation["password"])

                elif formatted_operation["op"] == "login":
                    self.login(formatted_operation["user"], formatted_operation["password"])

                elif formatted_operation["op"] == "encrypt":
                    self.encrypt(formatted_operation["file"])

                elif formatted_operation["op"] == "decrypt":
                    self.decrypt(formatted_operation["file"])

                elif formatted_operation["op"] == "help":
                    self.help()

    @staticmethod
    def help():
        print "The commands are:"
        print "['login'] - logs you in"
        print "['new-user' {user} {password}] - signs you in"
        print "['encrypt' {file}] - encrypts the file"
        print "['decrypt' {file}] - decrypts the file"
        print "['help'] - list of commands"

    @staticmethod
    def format_input(string):
        fragmented_input = string.split(" ")
        if len(fragmented_input) == 3:
            return json.dumps({"op": fragmented_input[0], "user": fragmented_input[1], "password": fragmented_input[2]})
        elif len(fragmented_input) == 2:
            return json.dumps({"op": fragmented_input[0], "file": fragmented_input[1]})
        else:
            return json.dumps({"op": fragmented_input[0]})

    def new_user(self, user, password):
        self.ssl_socket.write(json.dumps({"op": "new-user", "data": {"user": user, "password": password}}))

        json_data = self.ssl_socket.read()
        data = json.loads(json_data)
        if data["op"] == "ok":
            print "new user successfully signed in"
            self.user = user
            self.password = password

    def login(self, user, password):
        self.ssl_socket.write(json.dumps({"op": "login", "data": {"user": user, "password": password}}))
        json_data = self.ssl_socket.read()
        data = json.loads(json_data)
        if data["op"] == "ok":
            self.session = data["data"]["session id"]
            print "successfully logged in"
        else:
            if "error" in data["data"]:
                print data["data"]["error"]
            else:
                print "unknown error, the input was - {}".format(json_data)

    def encrypt(self, e_file):
        self.ssl_socket.write(json.dumps({"op": "new-key", "data": {"session": self.session}}))

        json_data = self.ssl_socket.read()
        data = json.loads(json_data)
        if data["op"] == "key":
            curr_key = data["data"]["key"]
            print "got a new key"

            # do encryption
            key_id = hashlib.sha512(e_file).hexdigest()

            while True:
                self.ssl_socket.write(
                    json.dumps({"op": "set-hash", "data": {"key-id": key_id, "session": self.session}}))
                json_data = self.ssl_socket.read()
                data = json.loads(json_data)
                if data["op"] == "ok":
                    print "successfully encrypted"
                    break
        else:
            if "error" in data["data"]:
                print data["data"]["error"]
            else:
                print "unknown error, the input was - {}".format(json_data)

    def decrypt(self, e_file):
        key_id = hashlib.sha512(e_file).hexdigest()
        self.ssl_socket.write(json.dumps({"op": "get-key", "data": {"key-id": key_id, "session": self.session}}))

        json_data = self.ssl_socket.read()
        data = json.loads(json_data)
        if data["op"] == "key":
            curr_key = data["data"]["key"]

            # do decryption

            while True:
                self.ssl_socket.write(
                    json.dumps({"op": "del-key", "data": {"key-id": key_id, "session": self.session}}))

                json_data = self.ssl_socket.read()
                data = json.loads(json_data)
                if data["op"] == "ok":
                    print "successfully decrypted"
                    break
        else:
            if "error" in data["data"]:
                print data["data"]["error"]
            else:
                print "unknown error, the input was - {}".format(json_data)


Client().run()
