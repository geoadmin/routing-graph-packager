from typing import List, Tuple  # noqa: F401

from requests import Response
from starlette.testclient import TestClient

from routing_packager_app import SETTINGS
from routing_packager_app.utils.file_utils import make_package_path

DEFAULT_ARGS_POST = {
    "name": "test",
    "description": "test description",
    "bbox": "0,0,1,1",
    "router": "valhalla",
    "provider": "osm",
}


def create_new_user(client: TestClient, data: dict, auth_header, must_succeed=True) -> Response:
    """
    Helper function for valid new user creation.
    """
    response = client.post("/api/v1/users/", headers=auth_header, json=data)

    if must_succeed:
        res_json = response.json()
        assert (
            response.status_code == 200
        ), f"status code was {response.status_code} with {response.json()}"
        assert response.headers["Content-Type"] == "application/json"
        assert set(res_json.keys()) >= {"id", "email"}
        return response

    return response


def create_new_job(client, data, auth_header, must_succeed=True) -> Response:
    """
    Helper function for valid new job creation.
    """
    response = client.post("/api/v1/jobs/", headers=auth_header, json=data)

    if must_succeed:
        assert (
            response.status_code == 200
        ), f"status code was {response.status_code} with {response.content}"
        assert response.headers["Content-Type"] == "application/json"
        return response
    return response


def create_package_params(j):
    """
    Create the parameters for create_package task, with user ID 1.

    :param dict j: The job response in JSON

    :returns: Tuple with all parameters inside
    :rtype: tuple
    """
    data_dir = SETTINGS.DATA_DIR

    result_path = make_package_path(data_dir, j["name"], j["provider"])

    return (
        {},
        j["id"],
        j["name"],
        j["description"],
        j["bbox"],
        result_path,
        1
    )
