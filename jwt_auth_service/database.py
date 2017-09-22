# -*- coding: utf-8 -*-
import aioredis
from jwt_auth_service import config


class DB(object):
    _pool = None

    @classmethod
    async def create(cls):
        self = DB()
        self._pool = await aioredis.create_pool(
                ('localhost', 6379))
        return self

    async def execute(self, *args, **kwargs):
        return await self._pool.execute(*args, **kwargs)

    async def user_exists(self, username=None, email=None):
        exists = False
        with self._pool as redis:
            if username:
                return await redis.exists("{0}:user:{1}".format(config.DB_PREF, username))
            if email:
                return await redis.exists("{0}:email:{1}".format(config.DB_PREF, email))

            return exists

    async def save_user(self, user_data):
        """
        :param  user_data -> dist of user data
        Saves user to db
        """
        with self._pool as redis:
            new_user = False
            if not getattr(user_data, 'user_id'):
                while not redis.watch('current_user_id'):
                    continue
                user_id = redis.get('current_user_id')
                user_data['user_id'] = user_id + 1
                new_user = True

            db_user = "{0}:user:{1}".format(config.DB_PREF, user_data['user_id'])
            while not redis.watch(db_user):
                continue
            saved = redis.hmset(db_user, user_data)
            if saved & new_user:
                redis.incr('current_user_id')

            redis.unwatch()
            return user_data['user_id'] if saved else None

