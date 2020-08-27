from json.decoder import JSONDecodeError
import re
from typing import List
from base64 import b64encode

import pytest

from app.api_v1.users.models import User
"""Remember that @before_first_request will add an admin user!"""


def create_new_user(flask_app_client, data, auth_header, must_succeed=True):
    """
    Helper function for valid new user creation.
    """
    response = flask_app_client.post('/api/v1/users', headers=auth_header, data=data)

    if must_succeed:
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        assert set(response.json.keys()) >= {'id', 'email'}
        return response.json['id']
    return response


def delete_users(db, user_ids: List[int]):
    """Clean up after yourself!"""
    for idx in user_ids:
        user = User.query.get(idx)
        db.session.delete(user)
    db.session.commit()


def test_new_user_creation(flask_app_client, db, basic_auth_header):
    user_id = create_new_user(
        flask_app_client,
        auth_header=basic_auth_header,
        data={
            'email': "user1@email.com",
            'password': "user1_password",
        }
    )

    user1_instance = User.query.get(user_id)
    assert user1_instance.email == "user1@email.com"
    assert user1_instance.password == "user1_password"

    delete_users(db, [user_id])


def test_new_user_creation_duplicate_error(flask_app_client, db, basic_auth_header):
    # pylint: disable=invalid-name
    user_id = create_new_user(
        flask_app_client,
        auth_header=basic_auth_header,
        data={
            'email': "user1@email.com",
            'password': "user1_password",
        }
    )
    response = create_new_user(
        flask_app_client,
        auth_header=basic_auth_header,
        data={
            'email': "user1@email.com",
            'password': "user1_password",
        },
        must_succeed=False
    )
    assert response.status_code == 409
    assert response.content_type == 'application/json'
    assert response.json['error'] == 'Entity already exists...'

    delete_users(db, [user_id])


def test_new_user_invalid_field_error(flask_app_client, basic_auth_header):
    invalid_field = 'bogus_field'

    response = create_new_user(
        flask_app_client,
        auth_header=basic_auth_header,
        data={
            'email': "user1@email.com",
            'password': "user1_password",
            invalid_field: "bogus_value"
        },
        must_succeed=False
    )
    assert response.status_code == 400
    assert response.content_type == 'application/json'
    assert response.json['error'] == f'Unknown arguments: {invalid_field}'


@pytest.mark.parametrize('missing_field', ('email', 'password'))
def test_new_user_missing_field_error(missing_field, flask_app_client, basic_auth_header):
    data = {'email': "user1@email.com", 'password': "user1_password"}
    del data[missing_field]

    response = create_new_user(
        flask_app_client, auth_header=basic_auth_header, data=data, must_succeed=False
    )

    assert response.status_code == 400
    assert response.json['error'] == f"'{missing_field}' is required in request."


@pytest.mark.parametrize('email', ('user@email.12', 'user.me', 'uuser@email.c', 'user@email.'))
def test_new_user_wrong_email_error(email, flask_app_client, basic_auth_header):
    data = {'email': email, 'password': "user_password"}

    response = create_new_user(
        flask_app_client, auth_header=basic_auth_header, data=data, must_succeed=False
    )

    assert response.status_code == 400
    assert response.json['error'] == f'Email \'{email}\' is invalid.'


def test_new_user_no_admin_error(flask_app_client, db, basic_auth_header):
    email = 'user@email.org'
    password = 'password'

    new_user_id = create_new_user(
        flask_app_client, auth_header=basic_auth_header, data={
            'email': email,
            'password': password
        }
    )

    auth_encoded = b64encode(bytes(':'.join((email, password)).encode('utf-8'))).decode()
    auth_header = {'Authorization': f'Basic {auth_encoded}'}

    response = create_new_user(
        flask_app_client,
        auth_header=auth_header,
        data={
            'email': 'soemone@email.org',
            'password': 'bafa'
        },
        must_succeed=False
    )
    assert response.status_code == 403

    delete_users(db, [new_user_id])


def test_get_all_users_empty(flask_app_client):
    # Will still contain the admin user
    assert len(flask_app_client.get('/api/v1/users/').json) == 1


def test_get_all_users_not_empty(flask_app_client, db, basic_auth_header):
    user_ids = list()
    for i in range(3, 6):
        idx = create_new_user(
            flask_app_client,
            auth_header=basic_auth_header,
            data={
                "email": f'user{i}@email.com',
                "password": f'user{i}_password'
            }
        )
        user_ids.append(idx)

    response = flask_app_client.get('/api/v1/users/')

    assert len(response.json) == 4
    assert any('user4@email.com' in x['email'] for x in response.json)

    search_user = '^user[3|4|5]@email\.com$'
    search_pass = '^user[3|4|5]_password$'
    for i in user_ids:
        user = User.query.get(i)
        assert re.search(search_user, user.email)
        # assert re.search(search_pass, user.password)

    delete_users(db, user_ids)


def test_get_single_user(flask_app_client, db, basic_auth_header):
    user_id = create_new_user(
        flask_app_client,
        auth_header=basic_auth_header,
        data={
            'email': "userx@email.com",
            'password': "userx_password"
        }
    )

    response = flask_app_client.get(f'/api/v1/users/{user_id}')

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert response.json['email'] == 'userx@email.com'

    delete_users(db, [user_id])


def test_get_single_user_not_found(flask_app_client):
    response = flask_app_client.get('/api/v1/users/2')

    assert response.status_code == 404
    assert response.content_type == 'application/json'
    assert response.json['error'] == 'Entity not found.'


def test_delete_single_user(flask_app_client, basic_auth_header):
    create_new_user(
        flask_app_client,
        auth_header=basic_auth_header,
        data={
            'email': "usery@email.com",
            'password': "usery_password"
        }
    )

    user_before = User.query.filter_by(email='usery@email.com').first()
    assert user_before.password == "usery_password"

    response = flask_app_client.delete(f'/api/v1/users/{user_before.id}', headers=basic_auth_header)

    assert response.status_code == 204
    # Empty response means `json` will fail to parse
    with pytest.raises(JSONDecodeError):
        assert response.json == None

    user_after = User.query.filter_by(email='usery@email.com').first()
    assert user_after is None


def test_delete_single_user_not_found(flask_app_client, basic_auth_header):
    response = flask_app_client.delete('/api/v1/users/2', headers=basic_auth_header)

    assert response.status_code == 404
    assert response.content_type == 'application/json'
    assert response.json['error'] == 'Entity not found.'


def test_delete_admin_error(flask_app_client, basic_auth_header):
    response = flask_app_client.delete('/api/v1/users/1', headers=basic_auth_header)

    assert response.status_code == 409
    assert response.json['error'] == "Can't delete admin user."


def test_delete_auth_no_admin_error(flask_app_client, db, basic_auth_header):
    email = 'user@email.org'
    password = 'password'

    new_user_id = create_new_user(
        flask_app_client, auth_header=basic_auth_header, data={
            'email': email,
            'password': password
        }
    )

    auth_encoded = b64encode(bytes(':'.join((email, password)).encode('utf-8'))).decode()
    auth_header = {'Authorization': f'Basic {auth_encoded}'}

    response = flask_app_client.delete(f'/api/v1/users/{new_user_id}', headers=auth_header)

    assert response.status_code == 403
    assert response.json['error'] == "Admin privileges are required to delete a user."


def test_admin_user_created(flask_app_client, flask_app):
    """Tests whether the admin user was created before the first request"""
    expected_email = flask_app.config['ADMIN_EMAIL']
    expected_pass = flask_app.config['ADMIN_PASS']

    print(expected_email, expected_pass)

    response = flask_app_client.get('/api/v1/users')
    assert response.json[0]['email'] == expected_email

    admin_user = User.query.get(1)
    assert admin_user.email == expected_email
    assert admin_user.password == expected_pass


def test_basic_auth_no_auth(flask_app_client):
    response = flask_app_client.post(
        '/api/v1/users/', data={
            'email': "userx@email.com",
            'password': "userx_password"
        }
    )

    assert response.status_code == 401
    assert b'"Missing Basic Auth authorization header."' in response.data


def test_basic_auth_wrong_auth(flask_app_client):
    auth = ('gis', 'ops')
    auth_encoded = b64encode(bytes(':'.join((auth)).encode('utf-8'))).decode()
    auth_header = {'Authorization': f'Basic {auth_encoded}'}
    response = flask_app_client.post(
        '/api/v1/users/',
        headers=auth_header,
        data={
            'email': "userx@email.com",
            'password': "userx_password"
        }
    )

    assert response.status_code == 401
    assert b'"Missing Basic Auth authorization header."' in response.data
