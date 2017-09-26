# -*- coding: utf-8 -*-
import aioredis
from jwt_auth_service import config


class DB(object):
    _pool = None

    @classmethod
    async def create(cls):
        self = DB()
        self._pool = await aioredis.create_pool(
                ('localhost', 6379),
                minsize=5,
                encoding='utf-8')
        return self

    async def close(self):
        self._pool.close()
        await self._pool.wait_closed()

    async def execute(self, *args, **kwargs):
        return await self._pool.execute(*args, **kwargs)

    async def user_exists(self, username=None, email=None):
        with await self._pool as redis:
            user_id = False
            if username:
                user_id = await redis.hget("{0}:users".format(config.DB_PREF), username)
                if user_id:
                    int(user_id)
            # not implemented
            #if email:
            #   user_id = await redis.exists("{0}:emails:{1}".format(config.DB_PREF, email))
        return bool(user_id)

    async def get_id_by_username(self, username=''):
        if not username:
            return None
        source = "{0}:users".format(config.DB_PREF)
        with await self._pool as redis:
            id = await redis.hget(source, username)
            return int(id) if id else None

    async def get_user(self, id=None, username=None):
        with await self._pool as redis:
            if username:
                id = await self.get_id_by_username(username)
            if id:
                source = "{0}:user:{1}".format(config.DB_PREF, id)
                user_data = await redis.hgetall(source)
                if user_data:
                    user_data['user_id'] = id
                    user_data['is_admin'] = bool(int(user_data['is_admin']))
                return user_data
            return None

    async def save_user(self, user_data):
        """
        :param  user_data -> dist of user data
        Saves user to db
        """
        with await self._pool as redis:
            new_user = False
            if not getattr(user_data, 'user_id', None):
                while not await redis.watch('current_user_id'):
                    continue
                user_id = await redis.get('current_user_id') or 0
                user_data['user_id'] = int(user_id) + 1
                new_user = True

            db_user = "{0}:user:{1}".format(config.DB_PREF, user_data['user_id'])
            while not await redis.watch(db_user):
                continue
            #saved = await redis.hmset_dict(db_user, user_data)
            saved = await redis.hmset(db_user,
                                      'username', user_data['username'],
                                      'email', user_data['email'],
                                      'is_admin', int(user_data['is_admin']),
                                      'password', user_data['password'],)
            if saved & new_user:
                await redis.incr('current_user_id')
                await redis.hset("{0}:users".format(config.DB_PREF),
                                 user_data['username'],
                                 user_data['user_id'])

            await redis.unwatch()
            return user_data['user_id'] if saved else None

