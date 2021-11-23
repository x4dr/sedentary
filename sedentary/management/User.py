import json

from werkzeug.security import generate_password_hash,check_password_hash

from sedentary.serverside.DB_Abstraction import get_db


class User:
    def __init__(self, name: str):
        self.name: str = name
        self.is_authenticated = True  # assume every loaded user is authenticated
        self.is_loaded = False
        self.is_active = True
        self.is_anonymous = False
        self.pw_hash = None
        self.data = {}

    def get_id(self):
        return self.name

    def register(self, pw: str):
        if self.load() is not None:
            raise Exception("already registered")
        self.pw_hash = generate_password_hash(pw)
        self.is_authenticated = True
        self.save()

    def save(self):
        if not self.is_authenticated:
            raise Exception("not logged in")
        db = get_db()
        db.execute(
            "INSERT INTO user (username,pw_hash, data)  VALUES (?,?,?)",
            [self.name, self.pw_hash, json.dumps(self.data)],
        )
        db.commit()

    def load(self) -> "User":
        db = get_db()
        usr = db.execute(
            "SELECT pw_hash, data FROM user WHERE username=?", [self.name]
        ).fetchone()
        if usr is None:
            return None
        self.data = json.loads(usr[1])
        self.pw_hash = usr[0]
        self.is_loaded = True
        return self

    def login(self, p) -> "User":
        if not self.is_loaded:
            self.load()
        if check_password_hash(self.pw_hash, p):
            self.is_authenticated = True
        return self
