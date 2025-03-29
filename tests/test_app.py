import pytest
import json
from sqlalchemy import text
from app import create_app
from models import db, User
from werkzeug.security import generate_password_hash

# ------------------------ FIXTURES ------------------------

@pytest.fixture(scope="session")
def app():
    """
    Creates and configures a Flask app for testing purposes.

    The app is configured with testing settings, including a test database URI, 
    disabling tracking of modifications, and setting up JWT and cache configurations.
    
    The database schema is cleaned and reset before each test session, ensuring 
    no leftover data from previous tests.

    Yields:
        app: The Flask application instance with testing configurations.
    """
    app = create_app()
    app.config.update({
        'TESTING': True,  # Enables testing mode in Flask
        'SQLALCHEMY_DATABASE_URI': 'postgresql://admin:helloworld123@localhost/task_management_db',  # Test database URI
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,  # Disables modification tracking for performance
        'JWT_SECRET_KEY': 'super-secret',  # Secret key for JWT encoding/decoding
        'CACHE_TYPE': 'SimpleCache'  # Simple cache for performance enhancement during tests
    })

    with app.app_context():
        # Clean database by dropping and recreating the schema before running tests
        db.session.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        db.session.commit()
        
        db.create_all()  # Create all tables in the database
        yield app  # Yield the app instance for the test functions
        
        # Cleanup after tests: remove session and reset schema
        db.session.remove()
        db.session.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        db.session.commit()

@pytest.fixture(scope="function")
def client(app):
    """
    Provides a test client for interacting with the Flask application.

    The test client is used to make requests to the app without requiring 
    a live server.

    Args:
        app: The Flask app instance created by the `app` fixture.
    
    Yields:
        client: A test client that can be used to simulate HTTP requests.
    """
    return app.test_client()

@pytest.fixture(scope="function")
def auth_headers(client):
    """
    Provides authentication headers with a JWT token for authorized requests.

    This fixture creates a new user, logs them in, and retrieves a valid JWT token 
    that is then used for authorized API calls.

    Args:
        client: The Flask test client used to make requests.

    Yields:
        dict: The Authorization headers containing the JWT token.
    """
    with client.application.app_context():
        # Create a test user
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash=generate_password_hash('password123')
        )
        db.session.add(user)
        db.session.commit()
    
    # Perform login and get JWT token
    response = client.post('/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code == 200, f"Login failed: {response.data}"
    
    # Extract the JWT token from the response
    token = json.loads(response.data)['access_token']
    return {'Authorization': f'Bearer {token}'}

# ------------------------ TEST CASES ------------------------

def test_create_app(app):
    """
    Test the creation of the Flask app to ensure it's properly configured.

    Args:
        app: The Flask app instance created by the `app` fixture.
    
    Asserts:
        - App instance should not be None.
        - The app should be in testing mode.
    """
    assert app is not None
    assert app.config['TESTING'] is True

def test_login_success(client):
    """
    Test a successful login with correct credentials.

    This test creates a user, logs them in with valid credentials, and 
    checks that a valid JWT token is returned.

    Args:
        client: The Flask test client used to make requests.
    
    Asserts:
        - Status code should be 200.
        - The response should contain an access token.
    """
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
    """
    Test the login endpoint with missing fields (email or password).

    Args:
        client: The Flask test client used to make requests.
    
    Asserts:
        - Status code should be 400 for missing fields.
        - The error message should indicate missing email or password.
    """
    response = client.post('/login', json={'email': 'test@example.com'})
    assert response.status_code == 400
    assert 'Password is required' in json.loads(response.data)['error']

def test_login_invalid_credentials(client):
    """
    Test the login endpoint with invalid credentials (wrong password).

    Args:
        client: The Flask test client used to make requests.
    
    Asserts:
        - Status code should be 401 for unauthorized access.
        - The error message should indicate invalid credentials.
    """
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
    assert 'Invalid password' in json.loads(response.data)['error']

def test_test_route_no_auth(client):
    """
    Test accessing a route that requires authentication without providing a JWT token.

    Args:
        client: The Flask test client used to make requests.
    
    Asserts:
        - Status code should be 401 for unauthorized access.
    """
    response = client.get('/test')
    assert response.status_code == 401

def test_error_handlers(client):
    """
    Test the error handlers for various HTTP errors (404 in this case).

    Args:
        client: The Flask test client used to make requests.
    
    Asserts:
        - Status code should be 404 for non-existent routes.
        - The error message should indicate 'Not Found'.
    """
    response = client.get('/nonexistent-route')
    assert response.status_code == 404
    assert 'Not Found' in json.loads(response.data)['error']
