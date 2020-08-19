from json.decoder import JSONDecodeError
import pytest


def create_new_user(flask_app_client, data, must_succeed=True):
    """
    Helper function for valid new user creation.
    """
    response = flask_app_client.post('/api/v1/users/', data=data)

    if must_succeed:
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        assert set(response.json.keys()) >= {'id', 'email'}
        return response.json['id']
    return response


def cleanup_user_table(db):
    """Clean up after yourself!"""
    from app.api_v1.users.models import User
    users = User.query.all()
    for u in users:
        db.session.delete(u)
    db.session.commit()


def test_new_user_creation(flask_app_client, db):
    user_id = create_new_user(
        flask_app_client, data={
            'email': "user1@email.com",
            'password': "user1_password",
        }
    )
    assert isinstance(user_id, int)

    from app.api_v1.users.models import User

    user1_instance = User.query.get(user_id)
    assert user1_instance.email == "user1@email.com"
    assert user1_instance.password == "user1_password"

    cleanup_user_table(db)


def test_new_user_creation_duplicate_error(flask_app_client, db):
    # pylint: disable=invalid-name
    user_id = create_new_user(
        flask_app_client, data={
            'email': "user1@email.com",
            'password': "user1_password",
        }
    )
    response = create_new_user(
        flask_app_client,
        data={
            'email': "user1@email.com",
            'password': "user1_password",
        },
        must_succeed=False
    )
    assert response.status_code == 409
    assert response.content_type == 'application/json'
    assert response.json['error'] == 'Entity already exists, aborting..'

    cleanup_user_table(db)


def test_new_user_invalid_field_error(flask_app_client):
    invalid_field = 'bogus_field'

    response = create_new_user(
        flask_app_client,
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


def test_get_all_users_empty(flask_app_client):
    assert flask_app_client.get('/api/v1/users/').json == []


def test_get_all_users_not_empty(flask_app_client, db):
    for i in range(3, 6):
        create_new_user(
            flask_app_client, {
                "email": f'user{i}@email.com',
                "password": f'user{i}_password'
            }
        )

    response = flask_app_client.get('/api/v1/users/')

    assert len(response.json) == 3
    assert response.json[1]['id'] == 2
    assert response.json[1]['email'] == 'user4@email.com'

    cleanup_user_table(db)


def test_get_single_user(flask_app_client, db):
    create_new_user(flask_app_client, {'email': "userx@email.com", 'password': "userx_password"})

    response = flask_app_client.get('/api/v1/users/1')

    assert response.status_code == 200
    assert response.content_type == 'application/json'
    assert response.json == {'id': 1, 'email': 'userx@email.com'}

    cleanup_user_table(db)


def test_get_single_user_not_found(flask_app_client):
    response = flask_app_client.get('/api/v1/users/1')

    assert response.status_code == 404
    assert response.content_type == 'application/json'
    assert response.json['error'] == 'User not found.'


def test_delete_single_user(flask_app_client):
    create_new_user(flask_app_client, {'email': "usery@email.com", 'password': "usery_password"})

    from app.api_v1.users.models import User

    user_before = User.query.get(1)
    assert user_before.email == "usery@email.com"
    assert user_before.password == "usery_password"

    response = flask_app_client.delete('/api/v1/users/1')

    assert response.status_code == 204
    # Empty response means `json` will fail to parse
    with pytest.raises(JSONDecodeError):
        assert response.json == None

    user_after = User.query.get(1)
    assert user_after is None
