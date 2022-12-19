from fastapi.testclient import TestClient

from tests.utils import create_new_user


def test_client(get_client: TestClient, basic_auth_header):
    create_new_user(
        get_client, {"email": "usery@email.com", "password": "usery_password"}, basic_auth_header
    )
