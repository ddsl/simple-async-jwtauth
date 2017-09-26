
import pytest
from jwt_auth_service.database import DB


class TestDB:
    @pytest.mark.run_loop
    async def test_connection(self):
        db = DB.create()
        with db as redis:
            res = await redis.ping()
            print(res)
            assert res, "PONG"
        db.close()

    async def test_get_id_by_username(self):
        pass