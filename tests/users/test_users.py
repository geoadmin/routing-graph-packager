import re
from base64 import b64encode
from json import JSONDecodeError

import pytest
from sqlmodel import Session, select
from starlette.testclient import TestClient

from routing_packager_app import SETTINGS
from routing_packager_app.api_v1.models import User
from ..utils_ import create_new_user


def test_client(get_client: TestClient, basic_auth_header, get_session: Session, delete_users):
    user = {"email": "usery@email.com", "password": "usery_password"}
    create_new_user(get_client, user, basic_auth_header)

    user_db: User = get_session.exec(select(User).filter(User.email == user["email"])).first()
    assert user_db.email == user["email"]


def test_new_user_creation_duplicate_error(
    get_client: TestClient, basic_auth_header, get_session: Session
):
    user = {"email": "usery@email.com", "password": "usery_password"}
    create_new_user(
        get_client,
        user,
        basic_auth_header,
    )
    response = create_new_user(
        get_client,
        user,
        basic_auth_header,
        must_succeed=False,
    )
    assert response.status_code == 409
    assert response.headers["Content-Type"] == "application/json"
    assert response.json()["detail"] == "Key (email)=(usery@email.com) already exists."


@pytest.mark.parametrize("missing_field", ("email", "password"))
def test_new_user_missing_field_error(missing_field, get_client: TestClient, basic_auth_header):
    data = {"email": "user1@email.com", "password": "user1_password"}
    del data[missing_field]

    response = create_new_user(get_client, data, basic_auth_header, False)

    assert response.status_code == 422
    assert response.json()["detail"][0].get("msg") == "Field required"


@pytest.mark.parametrize("email", ("user@email.12", "user.me", "uuser@email:", "user@email."))
def test_new_user_wrong_email_error(email, get_client: TestClient, basic_auth_header):
    data = {"email": email, "password": "user_password"}

    response = create_new_user(get_client, auth_header=basic_auth_header, data=data, must_succeed=False)

    assert response.status_code == 422
    assert response.json()["detail"][0].get("msg")[:34] == "value is not a valid email address"


def test_new_user_unauthorized(get_client, basic_auth_header):
    email = "user@email.org"
    password = "password"

    create_new_user(
        get_client, auth_header=basic_auth_header, data={"email": email, "password": password}
    )

    auth_encoded = b64encode(bytes(":".join((email, password)).encode("utf-8"))).decode()
    auth_header = {"Authorization": f"Basic {auth_encoded}"}

    response = create_new_user(
        get_client,
        auth_header=auth_header,
        data={"email": "soemone@email.org", "password": "bafa"},
        must_succeed=False,
    )
    assert response.status_code == 401


def test_new_user_forbidden(get_client):
    response = create_new_user(
        get_client,
        auth_header={},
        data={"email": "soemone@email.org", "password": "bafa"},
        must_succeed=False,
    )

    assert response.status_code == 401


def test_get_all_users_empty(get_client: TestClient):
    # Will still contain the admin user
    assert len(get_client.get("/api/v1/users/").json()) == 1


def test_get_all_users_not_empty(get_client, basic_auth_header, get_session: Session):
    user_ids = list()
    for i in range(3, 6):
        res = create_new_user(
            get_client,
            auth_header=basic_auth_header,
            data={"email": f"user{i}@email.com", "password": f"user{i}_password"},
        )
        user_ids.append(res.json()["id"])

    response = get_client.get("/api/v1/users/")

    assert len(response.json()) == 4
    assert any("user4@email.com" in x["email"] for x in response.json())

    search_user = r"^user[3|4|5]@email\.com$"
    for i in user_ids:
        statement = select(User).where(User.id == i)
        user = get_session.exec(statement).first()
        assert user is not None
        assert re.search(search_user, user.email)


def test_get_single_user(get_client, basic_auth_header):
    res = create_new_user(
        get_client,
        auth_header=basic_auth_header,
        data={"email": "userx@email.com", "password": "userx_password"},
    )

    response = get_client.get(f"/api/v1/users/{res.json()['id']}")

    assert response.status_code == 200
    assert response.json()["email"] == "userx@email.com"


def test_get_single_user_not_found(get_client):
    response = get_client.get("/api/v1/users/2")

    assert response.status_code == 404
    assert response.json()["detail"] == "Couldn't find user id 2"


def test_delete_single_user(get_client, basic_auth_header, get_session: Session):
    create_new_user(
        get_client,
        auth_header=basic_auth_header,
        data={"email": "usery@email.com", "password": "usery_password"},
    )

    user_before = get_session.exec(select(User).filter_by(email="usery@email.com")).first()
    assert user_before.email == "usery@email.com"

    response = get_client.delete(f"/api/v1/users/{user_before.id}", headers=basic_auth_header)

    assert response.status_code == 204
    # Empty response means `json` will fail to parse
    with pytest.raises(JSONDecodeError):
        assert response.json() is None

    user_after = get_session.exec(select(User).filter_by(email="usery@email.com")).first()
    assert user_after is None


def test_delete_admin_error(get_client, basic_auth_header):
    response = get_client.delete("/api/v1/users/1", headers=basic_auth_header)

    assert response.status_code == 409
    assert response.json()["detail"] == "Can't delete admin user."


def test_delete_auth_no_admin_error(get_client, basic_auth_header):
    email = "user@email.org"
    password = "password"

    res = create_new_user(
        get_client, auth_header=basic_auth_header, data={"email": email, "password": password}
    )

    auth_encoded = b64encode(bytes(":".join((email, password)).encode("utf-8"))).decode()
    auth_header = {"Authorization": f"Basic {auth_encoded}"}

    response = get_client.delete(f"/api/v1/users/{res.json()['id']}", headers=auth_header)

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authorized to delete a user."


def test_admin_user_created(get_client, get_session: Session):
    """Tests whether the admin user was created before the first request"""
    expected_email = SETTINGS.ADMIN_EMAIL

    response = get_client.get("/api/v1/users")
    assert response.json()[0]["email"] == expected_email

    statement = select(User).where(User.id == 1)
    admin_user = get_session.exec(statement).first()
    assert admin_user is not None
    assert admin_user.email == expected_email
