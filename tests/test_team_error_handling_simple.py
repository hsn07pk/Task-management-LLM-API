import json
import os
import uuid
from unittest.mock import patch

import pytest
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash

from app import create_app
from models import Team, User, db


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


@pytest.fixture(scope="function")
def test_team(app, test_user):
    """
    Fixture to create a test team.
    """
    with app.app_context():
        # Create a team for testing
        team = Team(
            name=f"Test Team {uuid.uuid4().hex[:8]}",
            description="A test team for error handling testing",
            lead_id=uuid.UUID(test_user["id"]),
        )
        db.session.add(team)
        db.session.commit()

        # Return a dictionary with team information
        return {
            "id": str(team.team_id),
            "name": team.name,
            "description": team.description,
            "lead_id": str(team.lead_id),
        }


# Test for internal server error handling
@patch("routes.team_routes.TeamService.get_team")
def test_team_internal_error_handler(mock_get_team, client, auth_headers, test_team):
    """
    Test the internal server error handler for team routes.
    """
    # Configure the mock to return a tuple with an error response
    mock_get_team.return_value = ({"error": "Test internal server error"}, 500)

    # Make a request to get a team
    response = client.get(f"/teams/{test_team['id']}", headers=auth_headers)

    # Check the response
    assert response.status_code == 500
    data = json.loads(response.data)

    # Verify the error response format
    assert "error" in data
    assert "_links" in data
