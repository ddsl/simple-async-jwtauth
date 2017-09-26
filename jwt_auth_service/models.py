# -*- coding: utf-8 -*-
import bcrypt
from jwt_auth_service import config
#from jwt_auth_service import db

cfg = vars(config)


class User:

    def __init__(self, db, username, email, password, is_admin=False, user_id=None, hash_pwd=True):
        self.db = db
        self.user_id = user_id
        self.email = email
        self.password = password
        self.is_admin = is_admin
        self.username = username

        if hash_pwd:
            self.password = bcrypt.hashpw(
                password.encode(), bcrypt.gensalt(getattr(config, "BCRYPT_ROUNDS", 12))
            ).decode()
        else:
            self.password = password

    def __repr__(self):
        template = 'User id={s.user_id}: <{s.email}, is_admin={s.is_admin}>'
        return template.format(s=self)

    def __str__(self):
        return self.__repr__()

    def set_password(self, password):
        self.password = bcrypt.hashpw(
            password.encode(), bcrypt.gensalt(getattr(config, "BCRYPT_ROUNDS", 12))
        ).decode()

    def match_password(self, password):
        if bcrypt.hashpw(
                password.encode(), self.password.encode()
        ) != self.password.encode():
            raise self.PasswordDoesNotMatch()

    def verify_password(self, password):
        if bcrypt.hashpw(
                password.encode(), self.password.encode()
        ) == self.password.encode():
            return True
        else:
            return False

    async def save(self):
        user_id = await self.db.save_user(vars(self))
        if user_id > 0:
            self.user_id = user_id  # if new user then sets he's id
            return self
        else:
            return None



    class DoesNotExist(BaseException):
        pass

    class AlreadyExists(BaseException):
        pass

    class TooManyObjects(BaseException):
        pass

    class PasswordDoesNotMatch(BaseException):
        pass

    class Objects:
        _storage = []
        _max_id = 0

        @classmethod
        async def create(cls, db, username, email, password, is_admin=False):
            if await db.user_exists(username, email):
                raise User.AlreadyExists()
            else:
                return await User(db, username, email, password, is_admin).save()

        @classmethod
        def all(cls):
            return cls._storage

        @classmethod
        async def get(cls, db, user_id=None, username=None):
            user_data = await db.get_user(user_id, username)
            if user_data:
                return User(db, **user_data, hash_pwd=False)
            else:
                raise User.DoesNotExist()

        @classmethod
        async def save(cls, usr):
            return await usr.save()
