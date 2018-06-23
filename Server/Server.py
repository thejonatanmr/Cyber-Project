import json
import socket
import ssl
import threading
import uuid
import hashlib


# the input from the client is received as following:
# base64(operation:param1:param2)

# operations:
#   0 - acknowledge operation, params - 0::
#   1 - compress key request operation, params - 1::
#   2 - decompress key request operation, params - 2:keyId:
#   3 - new user operation, params - 3:user:password
#   4 - connection operation, params - 4:user:password

# the output the server sends is as following:
# base64(operation:params1:params2)
# operations:
#   0 - connected successfully, params - 0::
#   1 - failed to connect, params - {:}
#   2 - generated new key for compression, params - {key:keyId}
#   3 - deleted the key got decompression, params - {key:}

# the database is structured as the following:
# {user : {
#           password :
#           hash : {id1: key1, id2:key2, etc...}
#           }}

class ThreadedServer(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket()
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.users_database = {}
        self.keys_database = {}
        self.sessions = {}

    def listen(self):
        self.initialise_json()
        self.server_socket.listen(5)
        while True:
            new_socket, address = self.server_socket.accept()
            new_socket.settimeout(120)
            client = ssl.wrap_socket(new_socket, server_side=True, certfile="keys/server.crt",
                                     keyfile="keys/server.key")
            threading.Thread(target=self.listen_to_client, args=(client, address)).start()

    def listen_to_client(self, client, address):
        while True:
            try:
                json_data = client.read()
                if json_data:
                    data = json.loads(json_data)
                    if data["op"] == "login":
                        user, session = self.login(client, data["data"])

                    elif data["op"] == "new-key":
                        self.generate_new_key(client, data["data"])

                    elif data["op"] == "get-key":
                        self.get_key_with_id(client, data["data"])

                    elif data["op"] == "new-user":
                        self.new_user(client, data["data"])

                    elif data["op"] == "del-key":
                        self.delete_key(client, data["data"])

                    elif data["op"] == "set-hash":
                        self.set_hash(client, data["data"])

                else:
                    raise RuntimeError

            except RuntimeError:
                if session:
                    self.sessions.pop(session)
                client.shutdown(socket.SHUT_RDWR)
                client.close()
                print "a client disconnected"
                return False

    @staticmethod
    def send_user(client, data):
        client.write(json.dumps(data))

    @staticmethod
    def random_id():
        return str(uuid.uuid4())

    def set_hash(self, client, data):
        session = data["session"]
        if session not in self.sessions:
            self.send_user(client, self.phrase_output("failed", {"error": "you are not logged in"}))
            return False

        user = self.sessions[session][0]
        file_md5 = data["key-id"]
        key_id = self.generate_key_id(session, file_md5)
        key = self.users_database[user].pop("unsorted")
        self.keys_database[key_id] = key, data["start_seg"]
        self.update_keys_json()
        self.send_user(client, self.phrase_output("ok", {"message": "IDed the key"}))

    def generate_key_id(self, session, file_md5):
        m = hashlib.md5()
        user = self.sessions[session][0]
        password = self.sessions[session][1]
        m.update(file_md5)
        m.update(user)
        m.update(password)
        return m.hexdigest()

    def delete_key(self, client, data):
        session = data["session"]
        if session not in self.sessions:
            self.send_user(client, self.phrase_output("failed", {"error": "you are not logged in"}))
            return False

        file_id = self.generate_key_id(session, data["key-id"])
        if file_id in self.keys_database:
            self.keys_database.pop(file_id)
            self.send_user(client, self.phrase_output("ok"))
            self.update_keys_json()

    def generate_new_key(self, client, data):
        session = data["session"]
        if session not in self.sessions:
            self.send_user(client, self.phrase_output("failed", {"error": "you are not logged in"}))
            return False

        user = self.sessions[session][0]
        key = self.random_id()
        self.users_database[user]["unsorted"] = key
        self.send_user(client, self.phrase_output("key", {"key": key}))
        self.update_keys_json()

    def get_key_with_id(self, client, data):
        session = data["session"]
        if session not in self.sessions:
            self.send_user(client, self.phrase_output("failed", {"error": "you are not logged in"}))
            return False

        file_id = self.generate_key_id(session, data["key-id"])
        if file_id in self.keys_database:
            key = self.keys_database[file_id]
            self.send_user(client, self.phrase_output("key", {"key": key[0], "start_seg": key[1]}))

        else:
            self.send_user(client, self.phrase_output("failed", {"error": "key not found"}))

    def login(self, client, data):
        if data["user"] in self.users_database:
            if self.md5_string(data["password"]) == self.users_database[data["user"]]["password"]:
                session = self.random_id()
                self.sessions[session] = data["user"], data["password"]
                self.send_user(client, self.phrase_output("ok", {"session id": session}))
                return data["user"], session

    def new_user(self, client, data):
        if data["user"] in self.users_database:
            self.send_user(client, self.phrase_output("failed", {"error": "user exists"}))

        elif len(data["password"]) <= 3:
            self.send_user(client, self.phrase_output("failed", {"error": "password is too short"}))

        else:
            self.users_database[data["user"]] = {"password": self.md5_string(data["password"])}
            self.send_user(client, self.phrase_output("ok", {"message": "made new account"}))
            self.update_users_json()

    @staticmethod
    def md5_string(string):
        m = hashlib.md5()
        m.update(string)
        return m.hexdigest()

    @staticmethod
    def phrase_output(op, data={}):
        return {"op": op, "data": data}

    def initialise_json(self):
        with open("users.json", "r") as db:
            self.users_database = json.load(db)

        with open("keys.json", "r") as db:
            self.keys_database = json.load(db)

    def update_users_json(self):
        with open("users.json", "wb") as db:
            json.dump(self.users_database, db)

    def update_keys_json(self):
        with open("keys.json", "r") as db:
            json.dump(self.keys_database, db)


if __name__ == "__main__":
    ThreadedServer('0.0.0.0', 3075).listen()
