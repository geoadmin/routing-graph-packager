from base64 import b64encode

import pytest
from sqlmodel import Session, select

from routing_packager_app import SETTINGS
from routing_packager_app.api_v1.models import Job
from routing_packager_app.constants import Providers
from routing_packager_app.utils.file_utils import make_package_path
from ..utils_ import create_new_job, DEFAULT_ARGS_POST


def check_dir(job: Job):
    """Checks if a job directory exists and removes it after."""
    dir_ = SETTINGS.get_output_path()
    dir_.joinpath(f"{'_'.join([job.name, job.provider])}")

    assert dir_.exists() and dir_.is_dir()


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
    statement = select(Job).where(Job.id == res.json()["id"])
    job_inst: Job | None = get_session.exec(statement).first()

    assert job_inst is not None
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
        SETTINGS.get_output_path(), DEFAULT_ARGS_POST["name"], DEFAULT_ARGS_POST["provider"]
    )
    out_dir.mkdir(parents=True, exist_ok=False)

    job = create_new_job(
        get_client, auth_header=basic_auth_header, data=DEFAULT_ARGS_POST, must_succeed=False
    )

    assert job.status_code == 409


def test_job_get_jobs(get_client, basic_auth_header):
    create_new_job(get_client, auth_header=basic_auth_header, data={**DEFAULT_ARGS_POST})

    res = get_client.get("/api/v1/jobs/").json()

    assert isinstance(res, list) and len(res) == 1
    assert res[0]["zip_path"] == str(
        SETTINGS.get_output_path().joinpath("osm_test", "osm_test.zip").resolve()
    )


# parameterize the ones that should work with the default params
@pytest.mark.parametrize(
    "key_value",
    (("bbox", "0,0,1,1"), ("provider", "osm"), ("status", "Queued"), ("update", False)),
)
def test_job_get_jobs_all_params(key_value, get_client, basic_auth_header):
    # default
    create_new_job(get_client, auth_header=basic_auth_header, data={**DEFAULT_ARGS_POST})
    # won't be GET
    create_new_job(
        get_client,
        auth_header=basic_auth_header,
        data={
            "name": "test2",
            "provider": "tomtom",
            "bbox": "10,10,20,20",
            "update": True,
            "description": "blabla",
        },
    )

    res = get_client.get("/api/v1/jobs/", params=(key_value,)).json()

    # since we don't do any actual processing when testing, Statuses.Completed is never set
    assert isinstance(res, list) and len(res) == 2 if key_value[0] == "value" else 1
    assert res[0]["provider"] == "osm"


def test_job_get_job(get_client, basic_auth_header):
    res = create_new_job(get_client, auth_header=basic_auth_header, data={**DEFAULT_ARGS_POST})

    res = get_client.get(f"/api/v1/jobs/{res.json()['id']}").json()
    assert res["zip_path"] == str(
        SETTINGS.get_output_path().joinpath("osm_test", "osm_test.zip").resolve()
    )


def test_job_get_job_not_found(get_client, basic_auth_header):
    res = get_client.get("/api/v1/jobs/1")
    assert res.status_code == 404
    assert res.json()["detail"] == "Couldn't find job id 1"


def test_job_delete(get_client, basic_auth_header):
    res = create_new_job(get_client, auth_header=basic_auth_header, data={**DEFAULT_ARGS_POST})
    print(basic_auth_header)
    res = get_client.delete(f"/api/v1/jobs/{res.json()['id']}", headers=basic_auth_header)
    assert res.status_code == 204


def test_job_delete_invalid_auth(get_client, basic_auth_header):
    res = create_new_job(get_client, auth_header=basic_auth_header, data={**DEFAULT_ARGS_POST})

    res = get_client.delete(f"/api/v1/jobs/{res.json()['id']}", headers={})
    assert res.status_code == 401


def test_job_delete_invalid_pass(get_client, basic_auth_header):
    res = create_new_job(get_client, auth_header=basic_auth_header, data={**DEFAULT_ARGS_POST})

    res = get_client.delete(
        f"/api/v1/jobs/{res.json()['id']}",
        headers={"Authorization": "Basic YWRtaW5AZXhhbXBsZS5vcmc6YWRtaa5="},
    )
    assert res.status_code == 401
