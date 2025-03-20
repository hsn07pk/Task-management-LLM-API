import pytest
import json
from sqlalchemy import text
from app import create_app
from models import db, User
from werkzeug.security import generate_password_hash

@pytest.fixture(scope="session")
def app():
    """Create and configure a Flask app for testing."""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'postgresql://admin:helloworld123@localhost/task_management_db',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JWT_SECRET_KEY': 'super-secret',
        'CACHE_TYPE': 'SimpleCache'
    })

    with app.app_context():
        # Clean database before running tests
        db.session.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        db.session.commit()
        
        db.create_all()
        yield app
        
        db.session.remove()
        db.session.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        db.session.commit()

@pytest.fixture(scope="function")
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture(scope="function")
def auth_headers(client):
    """Get auth headers with JWT token."""
    with client.application.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash=generate_password_hash('password123')
        )
        db.session.add(user)
        db.session.commit()
    
    response = client.post('/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code == 200, f"Login failed: {response.data}"
    
    token = json.loads(response.data)['access_token']
    return {'Authorization': f'Bearer {token}'}

def test_create_app(app):
    """Test app creation."""
    assert app is not None
    assert app.config['TESTING'] is True

def test_login_success(client):
    """Test successful login."""
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
    response = client.post('/login', json={'email': 'test@example.com'})
    assert response.status_code == 400
    assert 'Missing email or password' in json.loads(response.data)['error']

def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
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


def test_test_route_no_auth(client):
    """Test the test route without authentication."""
    response = client.get('/test')
    assert response.status_code == 401


def test_error_handlers(client):
    """Test error handlers."""
    response = client.get('/nonexistent-route')
    assert response.status_code == 404
    assert 'Not Found' in json.loads(response.data)['error']
