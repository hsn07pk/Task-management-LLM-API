import pytest
from uuid import uuid4
from models import User
from flask_jwt_extended import create_access_token

def test_create_user(client):
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "Testpass123!",
        "role": "member"
    }
    response = client.post('/users', json=data)
    assert response.status_code == 201
    assert 'user_id' in response.json

def test_create_user_duplicate_email(client, test_user):
    data = {
        "username": "newuser",
        "email": test_user.email,
        "password": "Testpass123!"
    }
    response = client.post('/users', json=data)
    assert response.status_code == 400
    assert b'Email already exists' in response.data

def test_get_user(client, test_user):
    response = client.get(f'/users/{test_user.user_id}')
    assert response.status_code == 200
    assert response.json['username'] == test_user.username

def test_update_user_unauthorized(client, test_user):
    data = {"username": "newname"}
    response = client.put(f'/users/{test_user.user_id}', json=data)
    assert response.status_code == 403

def test_delete_user_as_admin(client, test_admin_user, test_user):
    # Get auth token for admin
    login_response = client.post('/login', json={
        "email": "alice@example.com",
        "password": "hashed_password_1"
    })
    token = login_response.json['access_token']
    
    response = client.delete(
        f'/users/{test_user.user_id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
