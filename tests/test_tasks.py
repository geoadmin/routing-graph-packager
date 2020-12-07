import os

import pytest
from flask import current_app
from werkzeug.exceptions import InternalServerError

from .utils import create_new_job, DEFAULT_ARGS_POST, create_package_params
from routing_packager_app.tasks import create_package
from routing_packager_app.utils.file_utils import make_package_path


@pytest.mark.parametrize('provider', ['osm', 'tomtom'])
def test_create_package(provider, flask_app_client, basic_auth_header, delete_jobs, handle_dirs):

    bbox = [1.542892, 42.508552, 1.574821, 42.53082]
    job = create_new_job(
        flask_app_client,
        {
            **DEFAULT_ARGS_POST,
            "name": provider,
            "bbox": ','.join([str(x) for x in bbox]),  # needs to be a real Andorra extent
        },
        basic_auth_header
    )

    create_package(*create_package_params(job), config_string='testing')


@pytest.mark.parametrize('compression', ['zip', 'tar.gz'])
def test_create_package_compressions(
    compression, flask_app_client, basic_auth_header, monkeypatch, delete_jobs, handle_dirs
):
    job = create_new_job(
        flask_app_client,
        {
            **DEFAULT_ARGS_POST,
            "name": compression,
            "compression": compression,
            "bbox": '1.542892,42.508552,1.574821,42.53082',  # needs to be a real Andorra extent
        },
        basic_auth_header
    )

    create_package(*create_package_params(job), config_string='testing')


def test_create_package_missing_pbf(
    flask_app_client, basic_auth_header, monkeypatch, delete_jobs, handle_dirs
):
    job1 = create_new_job(
        flask_app_client, {
            **DEFAULT_ARGS_POST, "bbox": '1.542892,42.508552,1.574821,42.53082'
        }, basic_auth_header
    )
    create_package(*create_package_params(job1), config_string='testing')

    # delete the PBF
    os.remove(job1["pbf_path"])

    with pytest.raises(InternalServerError) as e:
        create_package(*create_package_params(job1), config_string='testing')


# will fail right now since there might actually be a PBF 0,0,1,1 will extract smth from
# def test_create_package_empty_pbf(flask_app_client, basic_auth_header, delete_jobs, handle_dirs):
#     job = create_new_job(
#         flask_app_client,
#         {
#             **DEFAULT_ARGS_POST,
#             "bbox": '0,0,1,1',  # will produce an empty PBF
#         },
#         basic_auth_header
#     )
#
#     with pytest.raises(InternalServerError):
#         create_package(*create_package_params(job), config_string='testing')


def test_create_package_check_dirs(flask_app_client, basic_auth_header, delete_jobs, handle_dirs):
    router = 'valhalla'
    provider = 'osm'
    name = 'test'
    compression = 'zip'

    job = create_new_job(
        flask_app_client,
        {
            **DEFAULT_ARGS_POST,
            "router": router,
            "provider": provider,
            "name": name,
            "compression": "zip",
            "bbox": '1.542892,42.508552,1.574821,42.53082',  # needs to be a real Andorra extent
        },
        basic_auth_header
    )

    create_package(*create_package_params(job), config_string='testing', cleanup=False)

    app = flask_app_client.application
    data_dir = app.config['DATA_DIR']
    temp_dir = app.config['TEMP_DIR']

    # osmium's output
    cut_pbf_path = os.path.join(data_dir, provider, f'{job["id"]}.{provider}.pbf')
    assert os.path.isfile(cut_pbf_path), f'{cut_pbf_path} doesnt exist'

    # temp graphs/tiles
    graph_dir = os.path.join(temp_dir, router, 'graph')
    assert len(
        os.listdir(graph_dir)
    ) > 0, f'{graph_dir} has the following contents:\n{os.listdir(graph_dir)}'
    assert all([os.path.isdir(os.path.join(graph_dir, d)) for d in os.listdir(graph_dir)])

    # output package
    pkg_path = make_package_path(data_dir, name, router, provider, compression)
    assert os.path.isfile(pkg_path), f'{pkg_path} doesnt exist'

    # output meta JSON
    out_dir = os.path.dirname(pkg_path)
    fname = os.path.basename(pkg_path)
    fname_sanitized = fname.split(os.extsep, 1)[0]
    fp = os.path.join(out_dir, fname_sanitized + '.json')
    assert os.path.isfile(fp), f'{fp} doesnt exist'
