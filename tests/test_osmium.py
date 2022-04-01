import pytest
from shapely.geometry import Polygon
import os

from .utils import make_pbfs, DEFAULT_ARGS_POST, create_new_job, create_package_params
from routing_packager_app.osmium import get_pbfs_by_area  #
from routing_packager_app.tasks import create_package


def test_pbfs_by_area(tmpdir):
    # This will produce PBFs with bboxes in WGS84 degrees matching its features
    feats = {
        1: [[0, 0], [10, 10]],
        2: [[0, 0], [20, 20]],
        3: [[0, 0], [30, 30]],
    }

    paths = make_pbfs(tmpdir, feats)

    # A small polygon should return the smallest PBF
    paths_result = get_pbfs_by_area(tmpdir, Polygon([(0, 0), (0, 1), (1, 1), (1, 0)]))
    assert len(paths_result) == 3
    assert paths_result[0][0] == paths[1]  # should be the pbf path with the smallest bbox from feats


def test_pbfs_by_area_missing_pbf(tmpdir):
    feats = {
        1: [[0, 0], [10, 10]],
    }

    make_pbfs(tmpdir, feats)

    with pytest.raises(FileNotFoundError) as e:
        get_pbfs_by_area(tmpdir, Polygon([(50, 50), (50, 100), (100, 100), (100, 50)]))
        assert "No PBF found for bbox" == str(e)


def test_pbf_endpoint_success(tmpdir, flask_app_client, basic_auth_header, delete_jobs, handle_dirs):
    job = create_new_job(
        flask_app_client,
        {**DEFAULT_ARGS_POST, "bbox": "1.542892,42.508552,1.574821,42.53082"},
        basic_auth_header,
    )
    create_package(*create_package_params(job), config_string="testing")
    job_id = job["id"]

    r = flask_app_client.get(f"/api/v1/jobs/{job_id}/data/pbf").json

    expected_fields = ("filepath", "timestamp", "bbox")
    for f in expected_fields:
        assert f in r.keys()
        assert isinstance(r[f], str)
        assert len(r[f]) > 0
    assert "size" in r
    assert r["size"] in range(76700, 76800)

    os.remove(job["pbf_path"])


def test_pbf_endpoint_missing_job(flask_app_client, basic_auth_header, delete_jobs, handle_dirs):
    job = create_new_job(
        flask_app_client,
        {**DEFAULT_ARGS_POST, "bbox": "1.542892,42.508552,1.574821,42.53082"},
        basic_auth_header,
    )
    job_id = job["id"]

    if os.path.exists(job["pbf_path"]):
        os.remove(job["pbf_path"])

    r = flask_app_client.get(f"/api/v1/jobs/{job_id}/data/pbf")

    assert r.status_code == 404
    assert f"OSM file for job {job_id} not found." == r.json["error"]
