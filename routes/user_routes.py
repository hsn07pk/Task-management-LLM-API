import pytest
import json
import uuid
from datetime import datetime

def test_create_user(client):
    """Test creating a new user."""
    data = {
        'username': 'testuser',
        'email': 'testuser@example.com',
        'password_hash': 'hashed_password_test',
        'role': 'member'
    }
    
    response = client.post('/users', json=data)
    print("Create user response:", response.data)  # Debug print
    assert response.status_code == 201
    
    # Check response data
    response_data = json.loads(response.data)
    assert response_data['username'] == 'testuser'
    assert response_data['email'] == 'testuser@example.com'
    assert response_data['role'] == 'member'
    assert 'user_id' in response_data

def test_create_user_missing_required_fields(client):
    """Test creating a user with missing required fields."""
    data = {
        'username': 'incomplete_user'
    }
    
    response = client.post('/users', json=data)
    assert response.status_code == 400
    assert b'Missing required field' in response.data

def test_create_user_duplicate_username(client, test_user):
    """Test creating a user with a duplicate username."""
    data = {
        'username': test_user.username,
        'email': 'unique@example.com',
        'password_hash': 'hashed_password_test'
    }
    
    response = client.post('/users', json=data)
    assert response.status_code == 400
    assert b'Username already exists' in response.data

def test_create_user_invalid_email(client):
    """Test creating a user with an invalid email."""
    data = {
        'username': 'validuser',
        'email': 'invalid-email',
        'password_hash': 'hashed_password_test'
    }
    
    response = client.post('/users', json=data)
    assert response.status_code == 400
    assert b'Invalid email format' in response.data

def test_get_all_users(client, test_user):
    """Test getting all users."""
    response = client.get('/users')
    print("Get all users response:", response.data)  # Debug print
    assert response.status_code == 200
    
    # Check response data
    users = json.loads(response.data)
    assert isinstance(users, list)
    assert len(users) > 0
    assert any(user['username'] == test_user.username for user in users)

def test_get_single_user(client, test_user):
    """Test getting a single user."""
    response = client.get(f'/users/{test_user.user_id}')
    assert response.status_code == 200
    
    # Check response data
    user = json.loads(response.data)
    assert user['user_id'] == str(test_user.user_id)
    assert user['username'] == test_user.username
    assert user['email'] == test_user.email

def test_get_nonexistent_user(client):
    """Test getting a user that doesn't exist."""
    response = client.get(f'/users/{uuid.uuid4()}')
    assert response.status_code == 404

def test_update_user(client, test_user):
    """Test updating a user."""
    data = {
        'username': 'updated_username',
        'role': 'admin'
    }
    
    response = client.put(f'/users/{test_user.user_id}', json=data)
    assert response.status_code == 200
    
    # Check response data
    user = json.loads(response.data)
    assert user['username'] == 'updated_username'
    assert user['role'] == 'admin'

def test_update_nonexistent_user(client):
    """Test updating a user that doesn't exist."""
    data = {'username': 'new_username'}
    response = client.put(f'/users/{uuid.uuid4()}', json=data)
    assert response.status_code == 404

def test_update_user_invalid_role(client, test_user):
    """Test updating a user with invalid role."""
    data = {'role': 'invalid_role'}
    response = client.put(f'/users/{test_user.user_id}', json=data)
    print("Update user invalid role response:", response.data)  # Debug print
    assert response.status_code == 400

def test_delete_user(client, test_user):
    """Test deleting a user."""
    # Create a new user for deletion since test_user might be used by other tests
    data = {
        'username': 'user_to_delete',
        'email': 'delete@example.com',
        'password_hash': 'hashed_password_delete'
    }
    create_response = client.post('/users', json=data)
    created_user = json.loads(create_response.data)
    
    response = client.delete(f'/users/{created_user["user_id"]}')
    print("Delete user response:", response.data)  # Debug print
    assert response.status_code == 204
    
    # Verify user is deleted
    response = client.get(f'/users/{created_user["user_id"]}')
    assert response.status_code == 404

def test_delete_nonexistent_user(client):
    """Test deleting a user that doesn't exist."""
    response = client.delete(f'/users/{uuid.uuid4()}')
    assert response.status_code == 404