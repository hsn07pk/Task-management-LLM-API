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
    Creates and configures a Flask app for testing.

    The app is configured with testing settings, including a test database URI, 
    JWT secret, and cache configuration. The database schema is cleaned before 
    and after the tests to ensure no leftover data from previous test runs.

    Yields:
        app: The Flask application instance with test configurations.
    """
    app = create_app()
    app.config.update({
        'TESTING': True,  # Enables testing mode in Flask
        'SQLALCHEMY_DATABASE_URI': 'postgresql://admin:helloworld123@localhost/task_management_db',  # Test database URI
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,  # Disables modification tracking for performance
        'JWT_SECRET_KEY': 'super-secret',  # Secret key for JWT encoding/decoding
        'PRESERVE_CONTEXT_ON_EXCEPTION': False,  # Ensures no context is preserved on exceptions
        'CACHE_TYPE': 'SimpleCache'  # Simple cache configuration for testing purposes
    })

    with app.app_context():
        # Clean database by dropping and recreating the schema before running tests
        db.session.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        db.session.commit()
        
        db.create_all()  # Create all necessary tables in the test database
        yield app  # Yield the app instance for the test functions to use
        
        # Cleanup after tests: remove session and reset the schema
        db.session.remove()
        db.session.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        db.session.commit()

@pytest.fixture(scope="function")
def client(app):
    """
    Provides a test client to interact with the Flask app during tests.

    The test client is used to simulate HTTP requests to the Flask application 
    and capture responses, allowing for functional testing of the routes.

    Args:
        app: The Flask app instance created by the `app` fixture.

    Yields:
        client: A Flask test client instance used to send requests to the app.
    """
    return app.test_client()

@pytest.fixture(scope="function")
def auth_headers(client):
    """
    Provides authentication headers with a JWT token for authorized requests.

    This fixture simulates a user creation, logs the user in, and retrieves 
    a valid JWT token to be used for making authorized requests to the API.

    Args:
        client: The Flask test client instance used to simulate requests.

    Yields:
        dict: A dictionary containing the `Authorization` header with a 
        valid JWT token.
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
    
    # Perform login to retrieve the JWT token
    response = client.post('/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code == 200, f"Login failed: {response.data}"
    
    # Extract the JWT token from the login response
    token = json.loads(response.data)['access_token']
    return {'Authorization': f'Bearer {token}'}

# ------------------------ TEST CASES ------------------------

def test_create_app(app):
    """
    Test the app creation to ensure it's correctly configured for testing.

    Args:
        app: The Flask app instance created by the `app` fixture.
    
    Asserts:
        - The app instance should not be None.
        - The app should have testing mode enabled.
    """
    assert app is not None
    assert app.config['TESTING'] is True

def test_login_success(client):
    """
    Test a successful login with valid credentials.

    This test creates a user, logs them in with correct credentials, 
    and ensures a valid JWT token is returned.

    Args:
        client: The Flask test client instance used to simulate requests.
    
    Asserts:
        - Status code should be 200 for successful login.
        - The response should contain an `access_token`.
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
    Test login with missing fields (email or password).

    This test checks the behavior when the login request does not include 
    both email and password fields.

    Args:
        client: The Flask test client instance used to simulate requests.
    
    Asserts:
        - Status code should be 400 indicating a bad request due to missing fields.
        - The error message should indicate missing email or password.
    """
    response = client.post('/login', json={'email': 'test@example.com'})
    assert response.status_code == 400
    assert 'Missing email or password' in json.loads(response.data)['error']

def test_login_invalid_credentials(client):
    """
    Test login with invalid credentials (wrong password).

    This test checks the behavior when a user provides incorrect credentials 
    (wrong password).

    Args:
        client: The Flask test client instance used to simulate requests.
    
    Asserts:
        - Status code should be 401 indicating unauthorized access.
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
    assert 'Invalid credentials' in json.loads(response.data)['error']

def test_login_nonexistent_user(client):
    """
    Test login with a nonexistent user.

    This test checks the behavior when the user tries to log in with an 
    email that is not registered in the database.

    Args:
        client: The Flask test client instance used to simulate requests.
    
    Asserts:
        - Status code should be 401 indicating unauthorized access.
        - The error message should indicate invalid credentials.
    """
    response = client.post('/login', json={
        'email': 'nonexistent@example.com',
        'password': 'password123'
    })
    assert response.status_code == 401
    assert 'Invalid credentials' in json.loads(response.data)['error']

def test_test_route_no_auth(client):
    """
    Test the test route without authentication.

    This test ensures that routes requiring authentication return a 401 
    Unauthorized status when the user is not authenticated.

    Args:
        client: The Flask test client instance used to simulate requests.
    
    Asserts:
        - Status code should be 401 indicating unauthorized access.
    """
    response = client.get('/test')
    assert response.status_code == 401

def test_invalid_token(client):
    """
    Test accessing a protected route with an invalid token.

    This test checks how the app handles an invalid JWT token when trying 
    to access a protected route.

    Args:
        client: The Flask test client instance used to simulate requests.
    
    Asserts:
        - Status code should be 422 indicating a JWT decoding error.
    """
    response = client.get('/test', headers={
        'Authorization': 'Bearer invalid-token'
    })
    assert response.status_code == 422  # JWT decode error

def test_malformed_token(client):
    """
    Test accessing a protected route with a malformed token.

    This test checks how the app handles a malformed JWT token, which is 
    missing the actual token value.

    Args:
        client: The Flask test client instance used to simulate requests.
    
    Asserts:
        - Status code should be 422 indicating a malformed token.
    """
    response = client.get('/test', headers={
        'Authorization': 'Bearer'  # Missing token value
    })
    assert response.status_code == 422

def test_error_handlers(client):
    """
    Test error handlers for various HTTP errors.

    This test ensures that the app correctly handles 404 errors for 
    non-existent routes.

    Args:
        client: The Flask test client instance used to simulate requests.
    
    Asserts:
        - Status code should be 404 for non-existent routes.
        - The error message should indicate 'Not Found'.
    """
    response = client.get('/nonexistent-route')
    assert response.status_code == 404
    assert 'Not Found' in json.loads(response.data)['error']
