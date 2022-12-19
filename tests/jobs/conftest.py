import pytest
from sqlmodel import Session, select

from routing_packager_app.api_v1.models import Job


@pytest.yield_fixture(scope="function", autouse=True)
def delete_jobs(get_session: Session):
    yield
    jobs = get_session.exec(select(Job)).all()
    for job in jobs:
        get_session.delete(job)
        get_session.commit()
