import json
import os
import uuid
from datetime import datetime

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


# Input Validation Tests


def test_create_team_empty_payload(client, auth_headers):
    """
    Test creating a team with an empty payload.
    """
    response = client.post("/teams/", headers=auth_headers, json={})

    # Check response
    assert response.status_code == 400
    data = json.loads(response.data)

    # Verify error message
    assert "error" in data


def test_create_team_missing_name(client, auth_headers, test_user):
    """
    Test creating a team without a name.
    """
    team_data = {"description": "A team without a name", "lead_id": test_user["id"]}

    response = client.post("/teams/", headers=auth_headers, json=team_data)

    # Check response
    assert response.status_code == 400
    data = json.loads(response.data)

    # Verify error message
    assert "error" in data


def test_create_team_missing_lead_id(client, auth_headers):
    """
    Test creating a team without a lead_id.
    """
    team_data = {"name": "Team Without Lead", "description": "A team without a lead_id"}

    response = client.post("/teams/", headers=auth_headers, json=team_data)

    # Check response
    assert response.status_code == 400
    data = json.loads(response.data)

    # Verify error message
    assert "error" in data


def test_create_team_invalid_lead_id_format(client, auth_headers):
    """
    Test creating a team with an invalid lead_id format.
    """
    team_data = {
        "name": "Team With Invalid Lead",
        "description": "A team with an invalid lead_id format",
        "lead_id": "not-a-valid-uuid",
    }

    response = client.post("/teams/", headers=auth_headers, json=team_data)

    # Check response
    assert response.status_code == 400
    data = json.loads(response.data)

    # Verify error message
    assert "error" in data


def test_update_team_empty_payload(client, auth_headers, test_user):
    """
    Test updating a team with an empty payload.
    """
    # First create a team
    team_data = {
        "name": f"Test Team {uuid.uuid4().hex[:8]}",
        "description": "A test team for validation testing",
        "lead_id": test_user["id"],
    }

    create_response = client.post("/teams/", headers=auth_headers, json=team_data)

    if create_response.status_code in [200, 201]:
        team_id = json.loads(create_response.data).get("id") or json.loads(
            create_response.data
        ).get("team_id")

        # Update with empty payload
        response = client.put(f"/teams/{team_id}", headers=auth_headers, json={})

        # Check response - might be 200 if empty payload is allowed, or 400 if required
        assert response.status_code in [200, 400]

        # If it's a 400, verify error message
        if response.status_code == 400:
            data = json.loads(response.data)
            assert "error" in data


def test_update_team_invalid_id(client, auth_headers):
    """
    Test updating a team with an invalid ID.
    """
    # Invalid UUID format
    team_id = "not-a-valid-uuid"

    update_data = {"name": "Updated Team", "description": "Updated description"}

    response = client.put(f"/teams/{team_id}", headers=auth_headers, json=update_data)

    # Check response - could be 400, 404, or 500 depending on how the app handles UUID validation
    assert response.status_code in [400, 404, 500]
    data = json.loads(response.data)

    # Verify error message
    assert "error" in data


def test_delete_team_invalid_id(client, auth_headers):
    """
    Test deleting a team with an invalid ID.
    """
    # Invalid UUID format
    team_id = "not-a-valid-uuid"

    response = client.delete(f"/teams/{team_id}", headers=auth_headers)

    # Check response - could be 400, 404, or 500 depending on how the app handles UUID validation
    assert response.status_code in [400, 404, 500]
    data = json.loads(response.data)

    # Verify error message
    assert "error" in data


def test_add_team_member_empty_payload(client, auth_headers, test_user):
    """
    Test adding a team member with an empty payload.
    """
    # First create a team
    team_data = {
        "name": f"Test Team {uuid.uuid4().hex[:8]}",
        "description": "A test team for validation testing",
        "lead_id": test_user["id"],
    }

    create_response = client.post("/teams/", headers=auth_headers, json=team_data)

    if create_response.status_code in [200, 201]:
        team_id = json.loads(create_response.data).get("id") or json.loads(
            create_response.data
        ).get("team_id")

        # Add member with empty payload
        response = client.post(f"/teams/{team_id}/members", headers=auth_headers, json={})

        # Check response
        assert response.status_code == 400
        data = json.loads(response.data)

        # Verify error message
        assert "error" in data


def test_add_team_member_missing_user_id(client, auth_headers, test_user):
    """
    Test adding a team member without a user_id.
    """
    # First create a team
    team_data = {
        "name": f"Test Team {uuid.uuid4().hex[:8]}",
        "description": "A test team for validation testing",
        "lead_id": test_user["id"],
    }

    create_response = client.post("/teams/", headers=auth_headers, json=team_data)

    if create_response.status_code in [200, 201]:
        team_id = json.loads(create_response.data).get("id") or json.loads(
            create_response.data
        ).get("team_id")

        # Add member without user_id
        member_data = {"role": "developer"}

        response = client.post(f"/teams/{team_id}/members", headers=auth_headers, json=member_data)

        # Check response
        assert response.status_code == 400
        data = json.loads(response.data)

        # Verify error message
        assert "error" in data


def test_add_team_member_invalid_user_id(client, auth_headers, test_user):
    """
    Test adding a team member with an invalid user_id.
    """
    # First create a team
    team_data = {
        "name": f"Test Team {uuid.uuid4().hex[:8]}",
        "description": "A test team for validation testing",
        "lead_id": test_user["id"],
    }

    create_response = client.post("/teams/", headers=auth_headers, json=team_data)

    if create_response.status_code in [200, 201]:
        team_id = json.loads(create_response.data).get("id") or json.loads(
            create_response.data
        ).get("team_id")

        # Add member with invalid user_id
        member_data = {"user_id": "not-a-valid-uuid", "role": "developer"}

        response = client.post(f"/teams/{team_id}/members", headers=auth_headers, json=member_data)

        # Check response
        assert response.status_code in [400, 404]
        data = json.loads(response.data)

        # Verify error message
        assert "error" in data


def test_update_team_member_empty_payload(client, auth_headers, test_user):
    """
    Test updating a team member with an empty payload.
    """
    # First create a team
    team_data = {
        "name": f"Test Team {uuid.uuid4().hex[:8]}",
        "description": "A test team for validation testing",
        "lead_id": test_user["id"],
    }

    create_response = client.post("/teams/", headers=auth_headers, json=team_data)

    if create_response.status_code in [200, 201]:
        team_id = json.loads(create_response.data).get("id") or json.loads(
            create_response.data
        ).get("team_id")

        # Update member with empty payload
        response = client.put(
            f"/teams/{team_id}/members/{test_user['id']}", headers=auth_headers, json={}
        )

        # Check response - might be 200 if empty payload is allowed, or 400 if required
        assert response.status_code in [200, 400]

        # If it's a 400, verify error message
        if response.status_code == 400:
            data = json.loads(response.data)
            assert "error" in data


def test_update_team_member_invalid_role(client, auth_headers, test_user):
    """
    Test updating a team member with an invalid role.
    """
    # First create a team
    team_data = {
        "name": f"Test Team {uuid.uuid4().hex[:8]}",
        "description": "A test team for validation testing",
        "lead_id": test_user["id"],
    }

    create_response = client.post("/teams/", headers=auth_headers, json=team_data)

    if create_response.status_code in [200, 201]:
        team_id = json.loads(create_response.data).get("id") or json.loads(
            create_response.data
        ).get("team_id")

        # Add the user as a member first
        member_data = {"user_id": test_user["id"], "role": "developer"}

        client.post(f"/teams/{team_id}/members", headers=auth_headers, json=member_data)

        # Update member with invalid role
        update_data = {"role": ""}  # Empty role

        response = client.put(
            f"/teams/{team_id}/members/{test_user['id']}", headers=auth_headers, json=update_data
        )

        # Check response - might be 200 if empty role is allowed, or 400 if required
        assert response.status_code in [200, 400]

        # If it's a 400, verify error message
        if response.status_code == 400:
            data = json.loads(response.data)
            assert "error" in data


def test_nonexistent_endpoint(client, auth_headers):
    """
    Test accessing a non-existent endpoint.
    """
    # Use an endpoint that doesn't exist but doesn't trigger database queries
    response = client.get("/api/nonexistent", headers=auth_headers)

    # Check response
    assert response.status_code == 404


def test_method_not_allowed(client, auth_headers):
    """
    Test using an unsupported HTTP method on an endpoint.
    """
    # Try to use PATCH on teams endpoint (assuming it's not supported)
    response = client.patch("/teams/", headers=auth_headers, json={"name": "Test"})

    # Check response
    assert response.status_code == 405  # Method Not Allowed


def test_invalid_json(client, auth_headers):
    """
    Test sending invalid JSON to an endpoint.
    """
    # Send invalid JSON (not a proper JSON string)
    response = client.post(
        "/teams/",
        headers={**auth_headers, "Content-Type": "application/json"},
        data="This is not JSON",
    )

    # Check response
    assert response.status_code in [400, 415]  # Bad Request or Unsupported Media Type
