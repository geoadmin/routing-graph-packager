import pytest

from routing_packager_app.api_v1 import Job


@pytest.yield_fixture(scope='function', autouse=True)
def delete_jobs():
    yield
    Job.query.delete()
