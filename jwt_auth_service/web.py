# -*- coding: utf-8 -*-
import json
import asyncio
from datetime import datetime, timedelta
import jwt

from aiohttp import web
from jwt_auth_service.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXP_DELTA_SECONDS
from jwt_auth_service.database import DB
from jwt_auth_service.models import User


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
        user = await User.Objects.get(request.db, username=post_data['username'])
        user.match_password(post_data['password'])
    except (User.DoesNotExist, User.PasswordDoesNotMatch):
        return json_response({'message': 'Wrong credentials'}, status=400)

    payload = {
        'user_id': user.user_id,
        'exp': datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS)
    }
    jwt_token = jwt.encode(payload, JWT_SECRET, JWT_ALGORITHM)
    return json_response({'token': jwt_token.decode('utf-8')})

async def verify(request):
    post_data = await request.post()
    if 'token' in post_data:
        try:
            payload = jwt.decode(post_data['token'], JWT_SECRET, algorithms=JWT_ALGORITHM)
        except (jwt.DecodeError, jwt.ExpiredSignatureError):
            return json_response({'message': 'Token is invalid'}, status=400)
        return json_response({'message': 'Valid'}, status=200)
    return json_response({'message': 'Token not found'}, status=404)

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
        payload = {
            'user_id': user.user_id,
            'exp': datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS)
        }
        jwt_token = jwt.encode(payload, JWT_SECRET, JWT_ALGORITHM)
        return json_response({'message': 'user created',
                              'token': jwt_token.decode('utf-8')},
                             status=201)
    else:
        return json_response({'message': 'failed'})

async def auth_middleware(app, handler):
    async def middleware(request):
        request.user = None
        jwt_token = request.headers.get('authorization', None)
        if jwt_token:
            try:
                payload = jwt.decode(jwt_token, JWT_SECRET, algorithms=JWT_ALGORITHM)
            except (jwt.DecodeError, jwt.ExpiredSignatureError):
                return json_response({'message': 'Token is invalid'}, status=400)
            request.user = await User.Objects.get(db=request.db, user_id=payload['user_id'])
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

app = web.Application(middlewares=[db_injector_middleware,
                                   auth_middleware,])
loop = asyncio.get_event_loop()
app.db = loop.run_until_complete(init_db())

app.router.add_route('GET', '/get-user', get_user)
app.router.add_route('POST', '/login', login)
app.router.add_route('POST', '/register', register)
app.router.add_route('POST', '/verify', verify)

if __name__ == "__main__":
    web.run_app(app, host='localhost', port=8080)
