import json
import uuid

import pytest
from sqlalchemy import text
from werkzeug.security import check_password_hash, generate_password_hash

from app import create_app
from models import User, db


@pytest.fixture(scope="session")
def app():
    """
    Creates and configures a Flask application for testing purposes.

    This fixture sets up a PostgreSQL database for testing, clears the database schema
    before running tests, and ensures that all the tables are created before the tests
    begin. After tests are run, it cleans up by removing the schema and committing any
    changes to the database.

    Yields:
        app (Flask): The Flask application instance configured for testing.
    """
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "postgresql://admin:helloworld123@localhost/task_management_db",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "JWT_SECRET_KEY": "test-secret-key",
        }
    )

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
    """
    Provides a test client for the Flask app.

    This fixture creates a testing client that interacts with the app through
    HTTP requests. Each test is wrapped in a database transaction that is
    rolled back after the test to ensure isolation between tests.

    Args:
        app (Flask): The Flask application instance.

    Yields:
        testing_client (FlaskClient): The Flask test client instance.
    """
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
    """
    Provides authorization headers for making authenticated requests.

    This fixture creates a test user, logs them in, and returns the
    Authorization header containing a JWT token that can be used
    for authentication in subsequent requests.

    Args:
        client (FlaskClient): The Flask test client.
        app (Flask): The Flask application instance.

    Returns:
        dict: A dictionary containing the Authorization header with the JWT token.
    """
    # Create a test user with admin role
    with app.app_context():
        user = User(
            username="adminuser",
            email="admin@example.com",
            password_hash=generate_password_hash("adminpass"),
            role="admin",
        )
        db.session.add(user)
        db.session.commit()

    # Login and get token
    response = client.post("/login", json={"email": "admin@example.com", "password": "adminpass"})
    assert response.status_code == 200, f"Login failed: {response.data}"

    token = json.loads(response.data)["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_user(client, app):
    """
    Tests creating a new user.

    This test checks if a user can be successfully created by sending a POST
    request to the `/users` endpoint with a valid payload. It verifies that
    the user is created by checking the response status and the returned
    user data.

    Args:
        client (FlaskClient): The Flask test client.
        app (Flask): The Flask application instance.
    """
    with app.app_context():
        response = client.post(
            "/users",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "password123",
                "role": "member",
            },
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"


def test_create_user_duplicate_email(client, app):
    """
    Tests creating a user with a duplicate email.

    This test checks if an attempt to create a user with an email that
    already exists results in an appropriate error response.

    Args:
        client (FlaskClient): The Flask test client.
        app (Flask): The Flask application instance.
    """
    with app.app_context():
        # Create first user
        client.post(
            "/users",
            json={
                "username": "user1",
                "email": "duplicate@example.com",
                "password": "password123",
                "role": "member",
            },
        )

        # Try to create second user with the same email
        response = client.post(
            "/users",
            json={
                "username": "user2",
                "email": "duplicate@example.com",
                "password": "password123",
                "role": "member",
            },
        )
        assert response.status_code == 400
        assert "Email already exists" in json.loads(response.data)["error"]


def test_create_user_duplicate_username(client, app):
    """
    Tests creating a user with a duplicate username.

    This test checks if an attempt to create a user with a username that
    already exists results in an appropriate error response.

    Args:
        client (FlaskClient): The Flask test client.
        app (Flask): The Flask application instance.
    """
    with app.app_context():
        # Create first user
        client.post(
            "/users",
            json={
                "username": "sameusername",
                "email": "user1@example.com",
                "password": "password123",
                "role": "member",
            },
        )

        # Try to create second user with the same username
        response = client.post(
            "/users",
            json={
                "username": "sameusername",
                "email": "user2@example.com",
                "password": "password123",
                "role": "member",
            },
        )
        assert response.status_code == 400
        assert "Username already exists" in json.loads(response.data)["error"]


def test_create_user_invalid_data(client, app):
    """
    Tests creating a user with invalid data.

    This test checks if a user creation attempt with invalid data, such as
    an incorrectly formatted email, results in a 400 error and the expected
    error message.

    Args:
        client (FlaskClient): The Flask test client.
        app (Flask): The Flask application instance.
    """
    with app.app_context():
        response = client.post(
            "/users",
            json={
                "username": "invaliduser",
                "email": "invalid-email",  # Invalid email format
                "password": "password123",
            },
        )
        assert response.status_code == 400
        assert "Invalid request data" in json.loads(response.data)["error"]


def test_get_user(client, auth_headers, app):
    """
    Tests retrieving a user by ID.

    This test checks if a user can be successfully retrieved using their
    user ID, and verifies that the returned data matches the expected values.

    Args:
        client (FlaskClient): The Flask test client.
        auth_headers (dict): Authorization headers containing JWT token.
        app (Flask): The Flask application instance.
    """
    with app.app_context():
        # Create a user
        user = User(
            username="getuser",
            email="get@example.com",
            password_hash=generate_password_hash("password123"),
        )
        db.session.add(user)
        db.session.commit()
        user_id = user.user_id

        response = client.get(f"/users/{user_id}", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["username"] == "getuser"
        assert data["email"] == "get@example.com"
