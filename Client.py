import json
import socket
import ssl
import threading
import Queue
import hashlib


class Client:
    def __init__(self, server="localhost", port=3075):
        self.server = server
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ssl_socket = None
        self.user = ""
        self.session = ""
        self.operation_queue = Queue.Queue()

    @property
    def run(self):
        # Require a certificate from the server. We used a self-signed certificate
        # so here ca_certs must be the server certificate itself.
        self.ssl_socket = ssl_sock = ssl.wrap_socket(self.client_socket, ca_certs="keys/server.crt",
                                                     cert_reqs=ssl.CERT_REQUIRED)
        try:
            ssl_sock.connect((self.server, self.port))

            threading.Thread(target=self.user_worker).start()
            threading.Thread(target=self.server_worker).start()

        except:
            print "error connecting to the server"
            return False

    def user_worker(self):
        while True:
            raw_in = raw_input()
            self.format_input(raw_in)

    def server_worker(self):
        while True:
            if not self.operation_queue.empty():
                operation = self.operation_queue.get()
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
        print "['login' {user} {password}] - logs you in"
        print "['new-user' {user} {password}] - signs you in"
        print "['encrypt' {file}] - encrypts the file"
        print "['decrypt' {file}] - decrypts the file"
        print "['help'] - list of commands"

    def format_input(self, string):
        fragmented_input = string.split(" ")
        if len(fragmented_input) == 3:
            formatted_data = json.dumps(
                {"op": fragmented_input[0], "user": fragmented_input[1], "password": fragmented_input[2]})
        elif len(fragmented_input) == 2:
            formatted_data = json.dumps({"op": fragmented_input[0], "file": fragmented_input[1]})
        else:
            formatted_data = json.dumps({"op": fragmented_input[0]})
        self.operation_queue.put(formatted_data)

    def new_user(self, user, password):
        self.ssl_socket.write(json.dumps({"op": "new-user", "data": {"user": user, "password": password}}))

        json_data = self.ssl_socket.read()
        data = json.loads(json_data)
        if data["op"] == "ok":
            print "new user successfully signed in"
            self.user = user

    def login(self, user, password):
        self.ssl_socket.write(json.dumps({"op": "login", "data": {"user": user, "password": password}}))
        json_data = self.ssl_socket.read()
        data = json.loads(json_data)
        if data["op"] == "ok":
            self.session = data["data"]["session id"]
            print "successfully logged in, the session is {}".format(self.session)
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


Client().run
