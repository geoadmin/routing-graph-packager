import pytest
from sqlmodel import Session

from routing_packager_app.api_v1.models import Job
from routing_packager_app.constants import Providers
from ..utils import create_new_job, DEFAULT_ARGS_POST


@pytest.mark.parametrize("provider", Providers)
def test_post_job(provider, get_client, basic_auth_header, get_session: Session):
    job = create_new_job(
        get_client,
        auth_header=basic_auth_header,
        data={
            **DEFAULT_ARGS_POST,
            "provider": provider,
        },
    )

    job_inst: Job = get_session.query(Job).get(job["id"])

    # TODO: re-enable when other routers should be tested
    # assert job_inst.router == router
    assert job_inst.provider == provider
    assert job_inst.status == "Queued"
    assert job_inst.description == DEFAULT_ARGS_POST["description"]
    assert job_inst.user_id == 1
