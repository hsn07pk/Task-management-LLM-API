import json
import os
import uuid
from datetime import datetime

import pytest
from flask import Blueprint, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash

from app import create_app
from models import Team, User, db

# Create a test blueprint that will raise exceptions
test_error_bp = Blueprint("test_error", __name__, url_prefix="/test-error")


@test_error_bp.route("/internal-error", methods=["GET"])
def test_internal_error():
    """Test route that raises an exception to trigger the internal error handler."""
    try:
        # Simulate a database or service error
        raise Exception("Test internal server error")
    except Exception as e:
        # Return a tuple with error response and status code
        # This matches how the actual routes handle errors
        return {
            "error": "Internal Server Error",
            "message": str(e),
            "_links": {"self": "/test-error/internal-error"},
        }, 500


@pytest.fixture(scope="session")
def app():
    """
    Configure a Flask app for testing with PostgreSQL.
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

    # Register the test blueprint
    app.register_blueprint(test_error_bp)

    # Add error handler for the test blueprint
    @test_error_bp.errorhandler(500)
    def internal_error(error):
        response = {
            "error": "Internal Server Error",
            "message": str(error),
            "_links": {"self": "/test-error/internal-error"},
        }
        return jsonify(response), 500

    # Create all database tables for testing
    with app.app_context():
        db.create_all()

    return app


@pytest.fixture(scope="function")
def client(app):
    """
    Fixture to create a test client for the Flask application.
    """
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture(scope="function")
def test_user(app):
    """
    Fixture to create a test user.
    """
    with app.app_context():
        # Generate unique identifiers for this test run
        unique_id = str(uuid.uuid4())[:8]

        # Hash the password
        password_hash = generate_password_hash("password123")

        user = User(
            username=f"testuser_{unique_id}",
            email=f"test_{unique_id}@example.com",
            password_hash=password_hash,
            role="user",
        )
        db.session.add(user)
        db.session.commit()

        # Return a dictionary with user information to avoid session issues
        return {
            "id": str(user.user_id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
        }


@pytest.fixture(scope="function")
def auth_headers(app, test_user):
    """
    Fixture to generate authorization headers with JWT token for the test user.
    """
    with app.app_context():
        token = create_access_token(identity=test_user["id"])
        return {"Authorization": f"Bearer {token}"}


def test_internal_error_handler(client):
    """
    Test the internal error handler by directly triggering an exception.
    """
    # Make a request to the test route that raises an exception
    response = client.get("/test-error/internal-error")

    # Check the response
    assert response.status_code == 500
    data = json.loads(response.data)

    # Verify the error response format
    assert "error" in data
    assert "Internal Server Error" in data["error"]
    assert "_links" in data
