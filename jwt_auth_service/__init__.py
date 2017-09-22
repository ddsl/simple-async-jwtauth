# -*- coding: utf-8 -*-
import asyncio
from pkgutil import extend_path
from .database import DB

__path__ = extend_path(__path__, __name__)

#db = DB.create()  # aioredis.create_pool(('localhost', 6379))
