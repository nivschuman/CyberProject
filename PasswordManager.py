from Server import CommunicationProtocolServer
import pyodbc
import json
import base64
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from random import randbytes


# todo remove all sql injections
class PasswordManagerServer:
    def __init__(self, host, port, db_connection_string):
        self.server = CommunicationProtocolServer(host, port, 10800)  # session ttl is 3 hours
        self.db_connection = pyodbc.connect(db_connection_string)
        self.db_cursor = self.db_connection.cursor()

        self.server.handle_method("create_user", self.create_user)
        self.server.handle_method("login_request", self.login_request)
        self.server.handle_method("login_test", self.login_test)
        self.server.handle_method("get_password", self.get_password)
        self.server.handle_method("set_password", self.set_password)
        self.server.handle_method("delete_password", self.delete_password)

    def start_server(self):
        self.server.serve_forever()

    # receive json with publicKey, userName and create such user
    # returns ascii with info on success or error
    def create_user(self, req, res, session):
        body_str = req.body.decode("ascii")
        body_json = json.loads(body_str)

        public_key_bytes = base64.b64decode(body_json["publicKey"])
        user_name = body_json["userName"]

        # check if there already exists a user with given username
        public_key_str = f"0x{public_key_bytes.hex()}"
        self.db_cursor.execute(f"SELECT UserName, PublicKey FROM Users WHERE UserName=?", user_name)
        user_with_same_username = len(self.db_cursor.fetchall()) != 0
        self.db_cursor.execute(f"SELECT UserName, PublicKey FROM Users WHERE PublicKey=?", public_key_str)
        user_with_same_public_key = len(self.db_cursor.fetchall()) != 0

        if user_with_same_username:
            res.body = "User with this username already exists, choose a different username".encode("ascii")
        elif user_with_same_public_key:
            res.body = "User with this public key already exists, choose a different public key".encode("ascii")
        else:
            self.db_cursor.execute(f"INSERT INTO Users (UserName, PublicKey) VALUES (?, ?)", user_name, public_key_str)
            self.db_cursor.commit()
            res.body = "Successfully created user".encode("ascii")

        res.set_header_value("Content-Length", len(res.body))
        res.set_header_value("Method", "create_user")
        res.set_header_value("Content-Type", "ascii")

    # receive username in ascii and return encrypted random 64 bits, no body is returned on error
    def login_request(self, req, res, session):
        user_name = req.body.decode("ascii")

        # get user's public key from database
        self.db_cursor.execute(f"SELECT PublicKey FROM Users WHERE UserName=?", user_name)
        public_key_bytes = self.db_cursor.fetchall()

        # user does not exists or this was called without a session
        if len(public_key_bytes) == 0 or session is None:
            res.body = None
            res.set_header_value("Content-Length", 0)
        else:
            public_key_bytes = public_key_bytes[0][0]
            rsa_key = RSA.importKey(public_key_bytes)
            cipher = PKCS1_v1_5.new(rsa_key)

            # generate random 64 bit number and encrypt it
            random_number = randbytes(8)
            random_number_encrypted = cipher.encrypt(random_number)

            # return number in body
            res.body = random_number_encrypted
            res.set_header_value("Content-Length", len(res.body))

            # store number in session and user name
            session.data["loginNumber"] = random_number
            session.data["loginUserName"] = user_name

        res.set_header_value("Method", "login_request")
        res.set_header_value("Content-Type", "bytes")

    # receive decrypted 64 bits and if they match bits in session store logged in uid
    # returns ascii with info for success or failure
    def login_test(self, req, res, session):
        decrypted_number_bytes = req.body

        if session is None:
            res.body = "Failed - no session".encode("ascii")
        elif session.data.get("loginNumber") is None:
            res.body = "Failed - no login number in session".encode("ascii")
        elif session.data.get("loginUserName") is None:
            res.body = "Failed - no login username in session".encode("ascii")
        elif decrypted_number_bytes != session.data["loginNumber"]:
            res.body = "Failed - incorrect number".encode("ascii")
        else:  # correct number and data is in session
            # get user id from database
            user_name = session.data["loginUserName"]
            self.db_cursor.execute(f"SELECT ID FROM Users WHERE UserName=?", user_name)
            user_id = self.db_cursor.fetchall()

            if len(user_id) == 0:
                res.body = f"Failed - user {user_name} doesn't exist".encode("ascii")
            else:
                session.data["loggedInUID"] = user_id[0][0]
                res.body = "Succeeded".encode("ascii")

        res.set_header_value("Content-Length", len(res.body))
        res.set_header_value("Method", "login_test")
        res.set_header_value("Content-Type", "ascii")

    # returns json array of all sources tied to user in session. Return no body if error
    def get_sources(self, req, res, session):
        # no session
        if session is None:
            res.body = None
            res.set_header_value("Content-Length", 0)
            res.set_header_value("Method", "get_sources")

        # user is not logged in
        if session.data.get("loggedInUID") is None:
            res.body = None
            res.set_header_value("Content-Length", 0)
            res.set_header_value("Method", "get_sources")
            return

        user_id = session.data["loggedInUID"]

    # gets ascii string of password source and returns encrypted password, no body if error
    def get_password(self, req, res, session):
        source = req.body.decode("ascii")

        # no session
        if session is None:
            res.body = None
            res.set_header_value("Content-Length", 0)
            res.set_header_value("Method", "get_password")
            return

        # user is not logged in
        if session.data.get("loggedInUID") is None:
            res.body = None
            res.set_header_value("Content-Length", 0)
            res.set_header_value("Method", "get_password")
            return

        user_id = session.data["loggedInUID"]
        self.db_cursor.execute(f"SELECT Password FROM Passwords WHERE UserID=? AND Source=?", user_id, source)
        password = self.db_cursor.fetchall()

        # no password found
        if len(password) == 0:
            res.body = None
            res.set_header_value("Content-Length", 0)
            res.set_header_value("Method", "get_password")
            return

        password = password[0][0]

        res.body = password
        res.set_header_value("Content-Length", len(res.body))
        res.set_header_value("Method", "get_password")
        res.set_header_value("Content-Type", "bytes")

    # gets json of source and password encoded in base64, returns ascii if success or failure
    def set_password(self, req, res, session):
        body_str = req.body.decode("ascii")
        body_json = json.loads(body_str)

        source = body_json["source"]
        password = base64.b64decode(body_json["password"])
        password_str = f"0x{password.hex()}"

        # no session
        if session is None:
            res.body = "Failed - no session".encode("ascii")
            res.set_header_value("Content-Length", len(res.body))
            res.set_header_value("Method", "set_password")
            res.set_header_value("Content-Type", "ascii")
            return

        # user is not logged in
        if session.data.get("loggedInUID") is None:
            res.body = "Failed - not logged in".encode("ascii")
            res.set_header_value("Content-Length", len(res.body))
            res.set_header_value("Method", "set_password")
            res.set_header_value("Content-Type", "ascii")
            return

        user_id = session.data["loggedInUID"]

        # password for source already exists
        self.db_cursor.execute(f"SELECT Password FROM Passwords WHERE Source=? AND UserID=?", source, user_id)
        password = self.db_cursor.fetchall()
        if len(password) != 0:
            res.body = "Failed - password for source already exists".encode("ascii")
            res.set_header_value("Content-Length", len(res.body))
            res.set_header_value("Method", "set_password")
            res.set_header_value("Content-Type", "ascii")
            return

        # enter into database
        self.db_cursor.execute(f"INSERT INTO Passwords (Source, Password, UserID) VALUES (?, CONVERT(BINARY(256),?,1), ?)", source, password_str, user_id)
        self.db_cursor.commit()

        res.body = "Success".encode("ascii")
        res.set_header_value("Content-Length", len(res.body))
        res.set_header_value("Method", "set_password")
        res.set_header_value("Content-Type", "ascii")

    # gets source and deletes password record with given source. Returns ascii for success or failure
    def delete_password(self, req, res, session):
        source = req.body.decode("ascii")

        # no session
        if session is None:
            res.body = "Failed - no session".encode("ascii")
            res.set_header_value("Content-Length", len(res.body))
            res.set_header_value("Method", "delete_password")
            res.set_header_value("Content-Type", "ascii")
            return

        # user is not logged in
        if session.data.get("loggedInUID") is None:
            res.body = "Failed - not logged in".encode("ascii")
            res.set_header_value("Content-Length", len(res.body))
            res.set_header_value("Method", "delete_password")
            res.set_header_value("Content-Type", "ascii")
            return

        user_id = session.data["loggedInUID"]

        # password for source doesn't exists
        self.db_cursor.execute(f"SELECT Password FROM Passwords WHERE Source=? AND UserID=?", source, user_id)
        password = self.db_cursor.fetchall()
        if len(password) == 0:
            res.body = "Failed - password for source doesn't exist".encode("ascii")
            res.set_header_value("Content-Length", len(res.body))
            res.set_header_value("Method", "delete_password")
            res.set_header_value("Content-Type", "ascii")
            return

        # delete password record from database
        self.db_cursor.execute(f"DELETE FROM Passwords WHERE Source=? AND UserID=?", source, user_id)
        self.db_cursor.commit()

        res.body = "Success".encode("ascii")
        res.set_header_value("Content-Length", len(res.body))
        res.set_header_value("Method", "delete_password")
        res.set_header_value("Content-Type", "ascii")
