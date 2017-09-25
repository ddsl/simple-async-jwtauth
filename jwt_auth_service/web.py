# -*- coding: utf-8 -*-
import json
import asyncio
from datetime import datetime, timedelta
import jwt
import aiohttp
from aiohttp import web
import sys
print(sys.path)
from jwt_auth_service.database import DB
from jwt_auth_service.models import User


JWT_SECRET = 'secret'
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_SECONDS = 20


def json_response(body='', **kwargs):
    kwargs['body'] = json.dumps(body or kwargs['body']).encode('utf-8')
    kwargs['content_type'] = 'text/json'
    return web.Response(**kwargs)


def login_required(func):
    def wrapper(request):
        if not request.user:
            return json_response({'message': 'Auth required'}, status=401)
        return func(request)
    return wrapper


async def login(request):
    post_data = await request.post()

    try:
        user = User.Objects.get(email=post_data['email'])
        user.match_password(post_data['password'])
    except (User.DoesNotExist, User.PasswordDoesNotMatch):
        return json_response({'message': 'Wrong credentials'}, status=400)

    payload = {
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS)
    }
    jwt_token = jwt.encode(payload, JWT_SECRET, JWT_ALGORITHM)
    return json_response({'token': jwt_token.decode('utf-8')})


@login_required
async def get_user(request):
    return json_response({'user': str(request.user)})

async def register(request):
    post_data = await request.post()
    try:
        user = await User.Objects.create(request.db, **post_data)
    except User.AlreadyExists:
        return json_response({'message': 'User already exists'}, status=409)

    if user:
        return json_response({'message': 'user created'}, status=201)
    else:
        return json_response({'message': 'failed'})

async def auth_middleware(app, handler):
    async def middleware(request):
        request.user = None
        jwt_token = request.headers.get('authorization', None)
        if jwt_token:
            try:
                payload = jwt.decode(jwt_token, JWT_SECRET,
                                     algorithms=[JWT_ALGORITHM])
            except (jwt.DecodeError, jwt.ExpiredSignatureError):
                return json_response({'message': 'Token is invalid'},
                                     status=400)

            request.user = User.Objects.get(id=payload['user_id'])
        return await handler(request)
    return middleware

async def db_injector_middleware(app, handler):
    async def middleware(request):
        request.db = app.db
        return await handler(request)
    return middleware

async def init_db():
    db = await DB.create()
    return db

app = web.Application(middlewares=[auth_middleware,
                                   db_injector_middleware])
loop = asyncio.get_event_loop()
app.db = loop.run_until_complete(init_db())

app.router.add_route('GET', '/get-user', get_user)
app.router.add_route('POST', '/login', login)
app.router.add_route('POST', '/register', register)

if __name__ == "__main__":
    web.run_app(app, host='localhost', port=8080)
