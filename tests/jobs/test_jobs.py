from base64 import b64encode
from pathlib import Path

import pytest
from sqlmodel import Session

from routing_packager_app import SETTINGS
from routing_packager_app.api_v1.models import Job
from routing_packager_app.constants import Providers
from routing_packager_app.utils.file_utils import make_package_path
from ..utils import create_new_job, DEFAULT_ARGS_POST


def check_dir(job: Job):
    """Checks if a job directory exists and removes it after."""
    dir = Path(SETTINGS.DATA_DIR)
    dir.joinpath(f"{'_'.join([job.name, job.provider])}")

    assert dir.exists() and dir.is_dir()


@pytest.mark.parametrize("provider", Providers)
def test_post_job(provider, get_client, basic_auth_header, get_session: Session):
    res = create_new_job(
        get_client,
        auth_header=basic_auth_header,
        data={
            **DEFAULT_ARGS_POST,
            "provider": provider,
        },
    )

    job_inst: Job = get_session.query(Job).get(res.json()["id"])

    # TODO: re-enable when other routers should be tested
    # assert job_inst.router == router
    assert job_inst.provider == provider
    assert job_inst.status == "Queued"
    assert job_inst.description == DEFAULT_ARGS_POST["description"]
    assert job_inst.user_id == 1
    check_dir(job_inst)


def test_post_job_no_user(get_client):
    auth_encoded = b64encode(bytes(":".join(("blibla", "blub")).encode("utf-8"))).decode()
    bad_auth = {"Authorization": f"Basic {auth_encoded}"}
    job = create_new_job(get_client, auth_header=bad_auth, data=DEFAULT_ARGS_POST, must_succeed=False)

    assert job.status_code == 401


def test_post_job_existing_dir(get_client, basic_auth_header):
    out_dir = make_package_path(
        SETTINGS.DATA_DIR, DEFAULT_ARGS_POST["name"], DEFAULT_ARGS_POST["provider"]
    )
    out_dir.mkdir(parents=True, exist_ok=False)

    job = create_new_job(
        get_client, auth_header=basic_auth_header, data=DEFAULT_ARGS_POST, must_succeed=False
    )

    assert job.status_code == 409
