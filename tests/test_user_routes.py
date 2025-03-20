import pytest
import json
import uuid
from app import create_app
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text

@pytest.fixture(scope="session")
def app():
    """Create and configure a Flask app for testing with PostgreSQL."""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'postgresql://admin:helloworld123@localhost/task_management_db',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JWT_SECRET_KEY': 'test-secret-key'
    })
    
    with app.app_context():
        # Clean database schema before running tests
        db.session.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        db.session.commit()
        
        # Create all tables defined in models
        db.create_all()
        
        yield app
        
        # Clean up after all tests
        db.session.remove()
        db.session.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        db.session.commit()

@pytest.fixture(scope="function")
def client(app):
    """Test client for the app."""
    with app.test_client() as testing_client:
        with app.app_context():
            # Start a nested transaction for test isolation
            conn = db.engine.connect()
            trans = conn.begin()
            
            yield testing_client
            
            # Rollback the transaction after the test
            trans.rollback()
            conn.close()

@pytest.fixture(scope="function")
def auth_headers(client, app):
    """Get auth headers with JWT token."""
    # Create a test user with admin role
    with app.app_context():
        user = User(
            username='adminuser',
            email='admin@example.com',
            password_hash=generate_password_hash('adminpass'),
            role='admin'
        )
        db.session.add(user)
        db.session.commit()
    
    # Login and get token
    response = client.post('/login', json={
        'email': 'admin@example.com',
        'password': 'adminpass'
    })
    assert response.status_code == 200, f"Login failed: {response.data}"
    
    token = json.loads(response.data)['access_token']
    return {'Authorization': f'Bearer {token}'}

def test_create_user(client, app):
    """Test creating a new user."""
    with app.app_context():
        response = client.post('/users', json={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'password123'
        })
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['username'] == 'newuser'
        assert data['email'] == 'new@example.com'

def test_create_user_duplicate_email(client, app):
    """Test creating a user with duplicate email."""
    with app.app_context():
        # Create first user
        client.post('/users', json={
            'username': 'user1',
            'email': 'duplicate@example.com',
            'password': 'password123'
        })
        
        # Try to create second user with same email
        response = client.post('/users', json={
            'username': 'user2',
            'email': 'duplicate@example.com',
            'password': 'password123'
        })
        assert response.status_code == 400
        assert 'Email already exists' in json.loads(response.data)['error']

def test_create_user_duplicate_username(client, app):
    """Test creating a user with duplicate username."""
    with app.app_context():
        # Create first user
        client.post('/users', json={
            'username': 'sameusername',
            'email': 'user1@example.com',
            'password': 'password123'
        })
        
        # Try to create second user with same username
        response = client.post('/users', json={
            'username': 'sameusername',
            'email': 'user2@example.com',
            'password': 'password123'
        })
        assert response.status_code == 400
        assert 'Username already exists' in json.loads(response.data)['error']

def test_create_user_invalid_data(client, app):
    """Test creating a user with invalid data."""
    with app.app_context():
        response = client.post('/users', json={
            'username': 'invaliduser',
            'email': 'invalid-email',  # Invalid email format
            'password': 'password123'
        })
        assert response.status_code == 400
        assert 'Invalid request data' in json.loads(response.data)['error']

def test_get_user(client, auth_headers, app):
    """Test getting a user by ID."""
    with app.app_context():
        # Create a user
        user = User(
            username='getuser',
            email='get@example.com',
            password_hash=generate_password_hash('password123')
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.user_id
    
        response = client.get(f'/users/{user_id}', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['username'] == 'getuser'
        assert data['email'] == 'get@example.com'

# def test_get_nonexistent_user(client, auth_headers, app):
#     """Test getting a nonexistent user."""
#     with app.app_context():
#         response = client.get(f'/users/{uuid.uuid4()}', headers=auth_headers)
#         assert response.status_code == 404
#         assert 'User not found' in json.loads(response.data)['error']

# def test_update_user(client, auth_headers, app):
#     """Test updating a user."""
#     with app.app_context():
#         # Create a user
#         user = User(
#             username='updateuser',
#             email='update@example.com',
#             password_hash=generate_password_hash('password123')
#         )
#         db.session.add(user)
#         db.session.commit()
#         user_id = user.user_id
    
#         response = client.put(f'/users/{user_id}', headers=auth_headers, json={
#             'username': 'updateduser',
#             'email': 'updated@example.com',
#             'password': 'newpassword123'
#         })
#         assert response.status_code == 200
#         data = json.loads(response.data)
#         assert data['username'] == 'updateduser'
#         assert data['email'] == 'updated@example.com'
        
#         # Verify password was updated
#         updated_user = User.query.get(user_id)
#         assert check_password_hash(updated_user.password_hash, 'newpassword123')

# def test_delete_user(client, auth_headers, app):
#     """Test deleting a user."""
#     with app.app_context():
#         # Create a user
#         user = User(
#             username='deleteuser21212',
#             email='deleteuser21212@example.com',
#             password_hash=generate_password_hash('password123')
#         )
#         db.session.add(user)
#         db.session.commit()
#         user_id = user.user_id
    
#         response = client.delete(f'/users/{user_id}', headers=auth_headers)
#         assert response.status_code == 200
#         assert 'User deleted successfully' in json.loads(response.data)['message']
        
#         # Verify user was deleted
#         deleted_user = User.query.get(user_id)
#         assert deleted_user is None
