import json

from flask import Response
from flask.testing import Client
from werkzeug.utils import cached_property

DEFAULT_ARGS_POST = {
    "name": f"test",
    "description": 'test description',
    "bbox": "0,0,1,1",
    "router": 'valhalla',
    "provider": 'osm',
    "interval": 'once',
    "compression": 'zip',
}


class JSONResponse(Response):
    # pylint: disable=too-many-ancestors
    """
    A Response class with extra useful helpers, i.e. ``.json`` property.
    """
    @cached_property
    def json(self):
        return json.loads(self.get_data(as_text=True))


def create_new_user(flask_app_client, data, auth_header, must_succeed=True):
    """
    Helper function for valid new user creation.
    """
    response = flask_app_client.post('/api/v1/users', headers=auth_header, data=data)

    if must_succeed:
        assert response.status_code == 200, f"status code was {response.status_code} with {response.data}"
        assert response.content_type == 'application/json'
        assert set(response.json.keys()) >= {'id', 'email'}
        return response.json['id']
    return response


def create_new_job(client: Client, data, auth_header, must_succeed=True):
    """
    Helper function for valid new job creation.
    """
    response = client.post('/api/v1/jobs', headers=auth_header, data=data)

    if must_succeed:
        assert response.status_code == 200, f"status code was {response.status_code} with {response.data}"
        assert response.content_type == 'application/json'
        return response.json['id']
    return response
