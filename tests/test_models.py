from jwt_auth_service.models import User


class TestUser:
    async def test_creation(self):
        usr = await User.Objects.create('testuser', "test@test.com", '123')
        assert(usr.username, 'testuser')
        assert (usr.email, 'test@test.com')
        assert (usr.verify_password('123'))
