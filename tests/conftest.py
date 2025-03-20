import pytest
import json
from app import create_app
from models import db, User
from werkzeug.security import generate_password_hash

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JWT_SECRET_KEY': 'test-secret-key',
        'CACHE_TYPE': 'SimpleCache'
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def auth_headers(client):
    """Get auth headers with JWT token."""
    # Create a test user
    with client.application.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash=generate_password_hash('password123')
        )
        db.session.add(user)
        db.session.commit()
    
    # Login and get token
    response = client.post('/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    token = json.loads(response.data)['access_token']
    return {'Authorization': f'Bearer {token}'}

def test_create_app(app):
    """Test app creation."""
    assert app is not None
    assert app.config['TESTING'] is True

def test_login_success(client):
    """Test successful login."""
    # Create a test user
    with client.application.app_context():
        user = User(
            username='loginuser',
            email='login@example.com',
            password_hash=generate_password_hash('password123')
        )
        db.session.add(user)
        db.session.commit()
    
    response = client.post('/login', json={
        'email': 'login@example.com',
        'password': 'password123'
    })
    assert response.status_code == 200
    assert 'access_token' in json.loads(response.data)

def test_login_missing_fields(client):
    """Test login with missing fields."""
    response = client.post('/login', json={
        'email': 'test@example.com'
    })
    assert response.status_code == 400
    assert 'Missing email or password' in json.loads(response.data)['error']

def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    # Create a test user
    with client.application.app_context():
        user = User(
            username='invaliduser',
            email='invalid@example.com',
            password_hash=generate_password_hash('password123')
        )
        db.session.add(user)
        db.session.commit()
    
    response = client.post('/login', json={
        'email': 'invalid@example.com',
        'password': 'wrongpassword'
    })
    assert response.status_code == 401
    assert 'Invalid credentials' in json.loads(response.data)['error']

def test_test_route(client, auth_headers):
    """Test the test route with authentication."""
    response = client.get('/test', headers=auth_headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'Hello testuser' in data['message']
    assert 'user_id' in data

def test_test_route_no_auth(client):
    """Test the test route without authentication."""
    response = client.get('/test')
    assert response.status_code == 401

def test_fetch_users(client):
    """Test fetching all users with caching."""
    # Create some test users
    with client.application.app_context():
        for i in range(3):
            user = User(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password_hash=generate_password_hash('password123')
            )
            db.session.add(user)
        db.session.commit()
    
    response = client.get('/users')
    assert response.status_code == 200
    users = json.loads(response.data)
    assert len(users) >= 3
    assert 'username' in users[0]
    assert 'email' in users[0]

def test_error_handlers(client):
    """Test error handlers."""
    # Test 404 error
    response = client.get('/nonexistent-route')
    assert response.status_code == 404
    assert 'Not Found' in json.loads(response.data)['error']
