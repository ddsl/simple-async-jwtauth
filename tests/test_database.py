from jwt_auth_service.database import DB


class TestDB:
    async def test_connection(self):
        db = DB.create()
        with db as redis:
            res = await redis.ping()
            print(res)
            assert res, "PONG"
