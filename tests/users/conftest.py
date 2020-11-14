import pytest

from routing_packager_app.api_v1 import User


@pytest.yield_fixture(scope='function', autouse=True)
def delete_jobs():
    yield
    User.query.filter(User.id != 1).delete()
