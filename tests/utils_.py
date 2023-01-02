from typing import List, Tuple  # noqa: F401

from requests import Response
from starlette.testclient import TestClient

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
