import os

import pytest

from routing_packager_app.api_v1.jobs.models import Job
from routing_packager_app.constants import INTERVALS, COMPRESSIONS, ROUTERS, PROVIDERS, STATUSES
from routing_packager_app.utils.file_utils import make_package_path
from ..utils import create_new_job, DEFAULT_ARGS_POST


@pytest.mark.parametrize('router', ROUTERS)
@pytest.mark.parametrize('provider', PROVIDERS)
@pytest.mark.parametrize('interval', INTERVALS)
@pytest.mark.parametrize('compression', COMPRESSIONS)
def test_post_job(router, provider, interval, compression, flask_app_client, basic_auth_header):
    job = create_new_job(
        flask_app_client,
        auth_header=basic_auth_header,
        data={
            **DEFAULT_ARGS_POST, "router": router,
            "provider": provider,
            "interval": interval,
            "compression": compression
        }
    )

    job_inst: Job = Job.query.get(job['id'])

    assert job_inst.router == router
    assert job_inst.provider == provider
    assert job_inst.interval == interval
    assert job_inst.compression == compression
    assert job_inst.status == 'Queued'
    assert job_inst.description == DEFAULT_ARGS_POST['description']
    assert job_inst.user_id == 1

    pbf_dir = flask_app_client.application.config[provider.upper() + '_DIR']
    assert job_inst.pbf_path == os.path.join(pbf_dir, f"{job_inst.id}.{provider}.pbf")

    dataset_path = make_package_path(
        flask_app_client.application.config['DATA_DIR'], job_inst.name, router, provider,
        job_inst.compression
    )
    assert job_inst.path == dataset_path


@pytest.mark.parametrize(
    'wrong_param', [
        {
            'provider': 'blabla'
        },
        {
            'router': 'blabla'
        },
        {
            'interval': 'blabla'
        },
        {
            'compression': 'blabla'
        },
        {
            'bbox': ''
        },
        {
            'bbox': '1;2;3;4'
        },
        {
            'bbox': '1,2,3,blabla'
        },
    ]
)
def test_post_job_wrong_enum_parameters(wrong_param, flask_app_client, basic_auth_header):
    """Test one wrong parameter each time."""
    r = create_new_job(
        flask_app_client,
        auth_header=basic_auth_header,
        data={
            **DEFAULT_ARGS_POST,
            **wrong_param
        },
        must_succeed=False
    )

    assert r.status_code == 400

    wrong_p = list(wrong_param.keys())[0]
    error_msg = r.json['error']

    # parameter name should always be in the error message
    assert wrong_p in error_msg

    # bbox raises multiple errors
    if wrong_p == 'router':
        assert str(flask_app_client.application.config['ENABLED_ROUTERS']) in error_msg
    elif wrong_p == 'provider':
        assert str(flask_app_client.application.config['ENABLED_PROVIDERS']) in error_msg
    elif wrong_p == 'interval':
        assert str(INTERVALS) in error_msg
    elif wrong_p == 'compression':
        assert str(COMPRESSIONS) in error_msg


def test_job_bad_name(flask_app_client, basic_auth_header):
    r = create_new_job(
        flask_app_client, {
            **DEFAULT_ARGS_POST, "name": 'bad/name'
        },
        basic_auth_header,
        must_succeed=False
    )

    assert r.status_code == 400
    assert 'name' in r.json['error']


def test_post_job_existing_job_combo(flask_app_client, basic_auth_header):
    # First a job
    job = create_new_job(flask_app_client, auth_header=basic_auth_header, data=DEFAULT_ARGS_POST)

    r = create_new_job(
        flask_app_client, auth_header=basic_auth_header, data=DEFAULT_ARGS_POST, must_succeed=False
    )

    assert r.status_code == 409
    assert str(job['id']) in r.json['error']


def test_post_job_forbidden(flask_app_client):
    response = create_new_job(
        flask_app_client, auth_header={}, data=DEFAULT_ARGS_POST, must_succeed=False
    )

    assert response.status_code == 401


def test_get_jobs_all(flask_app_client, basic_auth_header):
    for router in ['valhalla', 'osrm', 'ors']:
        for provider in ['tomtom', 'osm']:
            for interval in ['once', 'daily']:
                for bbox in ['0,0,1,1', '2,2,3,3']:
                    r = create_new_job(
                        flask_app_client,
                        data={
                            **DEFAULT_ARGS_POST, "name": f"{router}, {provider}, {interval}, {bbox}",
                            "provider": provider,
                            "router": router,
                            "interval": interval,
                            "bbox": bbox
                        },
                        auth_header=basic_auth_header,
                        must_succeed=False
                    )

    # First get all 24 results
    r = flask_app_client.get('/api/v1/jobs')
    assert len(r.json) == 24

    # Then test all query string parameters
    r = flask_app_client.get('/api/v1/jobs', query_string={"interval": 'once'})
    assert len(r.json) == 12

    r = flask_app_client.get('/api/v1/jobs', query_string={"router": 'valhalla'})
    assert len(r.json) == 8

    r = flask_app_client.get('/api/v1/jobs', query_string={"provider": 'tomtom'})
    assert len(r.json) == 12

    r = flask_app_client.get('/api/v1/jobs', query_string={"status": 'Queued'})
    assert len(r.json) == 24

    r = flask_app_client.get('/api/v1/jobs', query_string={"status": 'Extracting'})
    assert len(r.json) == 0

    r = flask_app_client.get('/api/v1/jobs', query_string={"bbox": '0,0,1.5,1.5'})
    assert len(r.json) == 12


@pytest.mark.parametrize(
    'bbox', [
        {
            "bbox": '0,0,1,1',
            "count": 1
        },
        {
            "bbox": '0.5,0.5,0.75,0.75',
            "count": 1
        },
        {
            "bbox": '0.5,0.5,2.75,2.75',
            "count": 2
        },
        {
            "bbox": '0,0,4,4',
            "count": 2
        },
    ]
)
def test_get_jobs_bbox(bbox, flask_app_client, basic_auth_header):
    for box in ['0,0,1,1', '2,2,3,3']:
        create_new_job(
            flask_app_client,
            data={
                **DEFAULT_ARGS_POST, "name": f"{box}",
                "bbox": box
            },
            auth_header=basic_auth_header,
            must_succeed=False
        )

    r = flask_app_client.get('api/v1/jobs', query_string={"bbox": bbox['bbox']})

    assert len(r.json) == bbox['count']


def test_get_jobs_bad_status(flask_app_client):
    r = flask_app_client.get('/api/v1/jobs', query_string={'status': 'blabla'})

    assert r.status_code == 400
    assert str(STATUSES) in r.json['error']


def test_get_job(flask_app_client, basic_auth_header):
    job = create_new_job(flask_app_client, DEFAULT_ARGS_POST, basic_auth_header)

    r = flask_app_client.get(f'api/v1/jobs/{job["id"]}').json

    data_dir = flask_app_client.application.config['DATA_DIR']
    provider = DEFAULT_ARGS_POST['provider']

    del r['last_started']

    assert {
        **DEFAULT_ARGS_POST,
        "bbox": "0.0,0.0,1.0,1.0",  # App returns floats
        "status": 'Queued',
        "last_finished": None,
        "pbf_path": os.path.join(data_dir, provider, f"{r['id']}.{provider}.pbf"),
        "job_id": None,
        "id": job["id"],
        'path': os.path.join(data_dir, 'valhalla/valhalla_osm_test/valhalla_osm_test.zip'),
        "container_id": None,
        "user_id": 1
    } == r


def test_delete_job(flask_app_client, basic_auth_header):
    job = create_new_job(flask_app_client, DEFAULT_ARGS_POST, basic_auth_header)

    r = flask_app_client.delete(f'api/v1/jobs/{job["id"]}', headers=basic_auth_header)

    assert r.data == b''
    assert r.status_code == 204
