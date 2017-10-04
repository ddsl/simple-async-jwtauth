import asyncio
import pytest
import pytest_asyncio
from jwt_auth_service.database import DB

pytestmark = pytest.mark.asyncio
#can't execute as a fixture
@pytest.fixture(scope='module')
async def db_setup(request):
    print("\nconnect to db")
    db = await DB.create()
    async def resource_teardown():
        await db.close()
        print("\ndisconnect")

    request.addfinalizer(resource_teardown)
    return db


class TestDB:
    @pytest.mark.asyncio
    async def test_connection(self):
        db = await DB.create()
        with await db._pool as redis:
            res = await redis.ping()
            print(res)
            assert res, "PONG"
        await db.close()

    async def test_get_id_by_username(self):
        pass

    async def test_get_user(self):
        pass

    async def test_execute(self):
        pass

    async def test_user_exists(self):
        pass
