import json
import socket
import ssl
import threading
import uuid


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
        self.users = {}
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

        user = self.sessions[session]
        key_id = data["key-id"]
        key = self.users[user]["bash"].pop("unsorted")
        self.users[user]["bash"][key_id] = key
        self.update_json()
        self.send_user(client, self.phrase_output("ok", {"message": "IDed the key"}))

    def delete_key(self, client, data):
        session = data["session"]
        if session not in self.sessions:
            self.send_user(client, self.phrase_output("failed", {"error": "you are not logged in"}))
            return False

        user = self.sessions[session]
        if data["key-id"] in self.users[user]["bash"]:
            self.users[user]["bash"].pop(data["key-id"])
            self.send_user(client, self.phrase_output("ok"))
            self.update_json()

    def generate_new_key(self, client, data):
        session = data["session"]
        if session not in self.sessions:
            self.send_user(client, self.phrase_output("failed", {"error": "you are not logged in"}))
            return False

        user = self.sessions[session]
        key = self.random_id()
        # key_id = self.random_id()
        self.users[user]["bash"]["unsorted"] = key
        self.send_user(client, self.phrase_output("key", {"key": key}))  # , "key-id": key_id}))
        self.update_json()

    def get_key_with_id(self, client, data):
        session = data["session"]
        if session not in self.sessions:
            self.send_user(client, self.phrase_output("failed", {"error": "you are not logged in"}))
            return False

        user = self.sessions[session]
        if data["key-id"] in self.users[user]["bash"]:
            key = self.users[user]["bash"][data["key-id"]]
            self.send_user(client, self.phrase_output("key", {"key": key}))

        else:
            self.send_user(client, self.phrase_output("failed", {"error": "key not found"}))

    def login(self, client, data):
        if data["user"] in self.users:
            if data["password"] == self.users[data["user"]]["password"]:
                session = self.random_id()
                self.sessions[session] = data["user"]
                self.send_user(client, self.phrase_output("ok", {"session id": session}))
                return data["user"], session

    def new_user(self, client, data):
        if data["user"] in self.users:
            self.send_user(client, self.phrase_output("failed", {"error": "user exists"}))

        elif len(data["password"]) <= 3:
            self.send_user(client, self.phrase_output("failed", {"error": "password is too short"}))

        else:
            self.users[data["user"]] = {"password": data["password"], "bash": {}}
            self.send_user(client, self.phrase_output("ok", {"message": "made new account"}))
            self.update_json()

    @staticmethod
    def phrase_output(op, data={}):
        return {"op": op, "data": data}

    def initialise_json(self):
        with open("database.json", "r") as db:
            self.users = json.load(db)

    def update_json(self):
        with open("database.json", "wb") as db:
            json.dump(self.users, db)


if __name__ == "__main__":
    ThreadedServer('0.0.0.0', 3075).listen()
