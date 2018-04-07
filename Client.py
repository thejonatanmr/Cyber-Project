import socket, ssl, pprint, json

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Require a certificate from the server. We used a self-signed certificate
# so here ca_certs must be the server certificate itself.
ssl_sock = ssl.wrap_socket(client_socket, ca_certs="keys/server.crt", cert_reqs=ssl.CERT_REQUIRED)

ssl_sock.connect(('localhost', 3075))

ssl_sock.write(json.dumps({"op": "new-user", "data": {"user": "bob", "password": "1234"}}))
json_data = ssl_sock.read()
print json_data

ssl_sock.write(json.dumps({"op": "login", "data": {"user": "bob", "password": "1234"}}))
json_data = ssl_sock.read()
print json_data

data = json.loads(json_data)
session = data["data"]["session id"]

ssl_sock.write(json.dumps({"op": "new-key", "data": {"session": session}}))

json_data = ssl_sock.read()
print json_data

data = json.loads(json_data)

id = data["data"]["key-id"]
ssl_sock.write(json.dumps({"op": "get-key", "data": {"key-id": id, "session": session}}))

data = ssl_sock.read()
print data

ssl_sock.write(json.dumps({"op": "del-key", "data": {"key-id": id, "session": session}}))

data = ssl_sock.read()
print data

ssl_sock.close()
