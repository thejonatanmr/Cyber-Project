import json
import socket
import ssl
import threading
import uuid
import hashlib


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
        """Main server thread. waiting for new client connections and opening threads for each one"""
        self.initialise_json()
        self.server_socket.listen(5)
        while True:
            new_socket, address = self.server_socket.accept()
            new_socket.settimeout(120)
            client = ssl.wrap_socket(new_socket, server_side=True, certfile="keys/server.crt",
                                     keyfile="keys/server.key")
            threading.Thread(target=self.listen_to_client, args=(client, address)).start()

    def listen_to_client(self, client, address):
        """Main client thread loop. each client thread runs on this function."""
        while True:
            session = None
            try:
                json_data = client.read()
                if json_data:
                    data = json.loads(json_data)
                    if data["op"] == "login":
                        self.login(client, data["data"])

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

                    elif data["op"] == "close":
                        self.close_connection(client, data["data"])
                        return False
                else:
                    raise RuntimeError

            except Exception as e:
                print e
                if session:
                    self.sessions.pop(session)
                client.shutdown(socket.SHUT_RDWR)
                client.close()
                print "a client disconnected"
                return False

    @staticmethod
    def send_user(client, data):
        """Fromatting and sending data to user."""
        client.write(json.dumps(data))

    @staticmethod
    def generate_random_key(e_type):
        """Generates keys based on encryption type"""
        if e_type == 1:
            return str(uuid.uuid4())[0:16]
        elif e_type == 2:
            return str(uuid.uuid4())
        else:
            return False

    @staticmethod
    def random_id():
        """generates random id for sessions."""
        return str(uuid.uuid4())

    def close_connection(self, client, data):
        """Closes connection with a client"""
        session = data["session"]
        if session:
            self.sessions.pop(session)
        client.shutdown(socket.SHUT_RDWR)
        client.close()

    def set_hash(self, client, data):
        """Sets the key in the database based on a file-id from the user."""
        session = data["session"]
        if session not in self.sessions:
            self.send_user(client, self.phrase_output("failed", {"error": "you are not logged in"}))
            return False

        user = self.sessions[session][0]
        file_md5 = data["key-id"]
        key_id = self.generate_key_id(session, file_md5)
        key = self.users_database[user].pop("unsorted")
        self.keys_database[key_id] = key, data["start_seg"], data["e_type"]
        self.update_keys_json()
        self.update_users_json()
        self.send_user(client, self.phrase_output("ok", {"message": "IDed the key"}))

    def generate_key_id(self, session, file_md5):
        """Formatting and making the file-id into key-id"""
        m = hashlib.md5()
        user = self.sessions[session][0]
        password = self.sessions[session][1]
        full_str = file_md5 + user + password
        m.update(full_str)
        return m.hexdigest()

    def delete_key(self, client, data):
        """Deletes key from the database based on the file-id given"""
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
        """generates new key from a specific type and sends user"""
        session = data["session"]
        if session not in self.sessions:
            self.send_user(client, self.phrase_output("failed", {"error": "you are not logged in"}))
            return False

        user = self.sessions[session][0]

        key = self.generate_random_key(data["e_type"])
        if key == False:
            self.send_user(client, self.phrase_output("failed", {"error": "Could not detect encyption type"}))
            return False

        self.users_database[user]["unsorted"] = key
        self.send_user(client, self.phrase_output("key", {"key": key}))
        self.update_users_json()

    def get_key_with_id(self, client, data):
        """Gets file-id and sends the corresponding key to the client"""
        session = data["session"]
        if session not in self.sessions:
            self.send_user(client, self.phrase_output("failed", {"error": "you are not logged in"}))
            return False

        file_id = self.generate_key_id(session, data["key-id"])
        if file_id in self.keys_database:
            key = self.keys_database[file_id]
            self.send_user(client, self.phrase_output("key", {"key": key[0], "start_seg": key[1], "e_type": key[2]}))

        else:
            self.send_user(client, self.phrase_output("failed", {"error": "key not found"}))

    def login(self, client, data):
        """Checks the integrity of username and password of the user.
        makes a new session if ok, sends the user the new session.
        """
        if data["user"] in self.users_database:
            if self.md5_string(data["password"]) == self.users_database[data["user"]]["password"]:
                session = self.random_id()
                self.sessions[session] = data["user"], data["password"]
                self.send_user(client, self.phrase_output("ok", {"session id": session}))
        else:
            self.send_user(client,
                           self.phrase_output("failed", {"error": "bad login. the username or password were wrong"}))

    def new_user(self, client, data):
        """Checks the integrity of new username and password.
        saves the username and md5 of the password if ok.
        """
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
        """Takes a string and return the MD5 of that string"""
        m = hashlib.md5()
        m.update(string)
        return m.hexdigest()

    @staticmethod
    def phrase_output(op, data={}):
        """Formatting the data into a json for sending the client"""
        return {"op": op, "data": data}

    def initialise_json(self):
        """Reads the two databases"""
        with open("users.json", "r") as db:
            self.users_database = json.load(db)

        with open("keys.json", "r") as db:
            self.keys_database = json.load(db)

    def update_users_json(self):
        """Updates the users database"""
        with open("users.json", "wb") as db:
            json.dump(self.users_database, db)

    def update_keys_json(self):
        """Updates the keys database"""
        with open("keys.json", "wb") as db:
            json.dump(self.keys_database, db)


if __name__ == "__main__":
    ThreadedServer('0.0.0.0', 3075).listen()
