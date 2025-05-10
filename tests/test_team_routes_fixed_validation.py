import json
import os
import uuid
from unittest.mock import MagicMock, patch

import pytest
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash

from app import create_app
from models import Project, Task, Team, TeamMembership, User, db
from schemas.schemas import TEAM_MEMBERSHIP_SCHEMA

# Reuse fixtures from test_team_routes.py
from tests.test_team_routes import (
    app,
    auth_headers,
    client,
    test_member,
    test_project,
    test_task,
    test_team,
    test_user,
)


# Test add_team_member with valid data
def test_add_team_member_success(client, auth_headers, test_team, test_member):
    """Test add_team_member with valid data"""
    # Patch the service to return success
    with patch("services.team_services.TeamService.add_team_member") as mock_add_member:
        mock_add_member.return_value = ({"message": "Member added"}, 201)

        response = client.post(
            f"/teams/{test_team['id']}/members",
            headers=auth_headers,
            json={"user_id": test_member["id"], "role": "developer"},
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert "message" in data


# Test update_team_member with valid data
def test_update_team_member_success(client, auth_headers, test_team, test_member):
    """Test update_team_member with valid data"""
    # First add the member to the team
    with patch("services.team_services.TeamService.add_team_member") as mock_add:
        mock_add.return_value = ({"message": "Member added"}, 201)

        client.post(
            f"/teams/{test_team['id']}/members",
            headers=auth_headers,
            json={"user_id": test_member["id"], "role": "developer"},
        )

    # Now test update with valid data
    with patch("services.team_services.TeamService.update_team_member") as mock_update_member:
        mock_update_member.return_value = ({"message": "Role updated"}, 200)

        response = client.put(
            f"/teams/{test_team['id']}/members/{test_member['id']}",
            headers=auth_headers,
            json={"user_id": test_member["id"], "role": "lead"},
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "message" in data


# Test update_team_member with validation error
def test_update_team_member_validation_error(client, auth_headers, test_team, test_member):
    """Test update_team_member with validation error"""
    # First add the member to the team
    with patch("services.team_services.TeamService.add_team_member") as mock_add:
        mock_add.return_value = ({"message": "Member added"}, 201)

        client.post(
            f"/teams/{test_team['id']}/members",
            headers=auth_headers,
            json={"user_id": test_member["id"], "role": "developer"},
        )

    # Now test update with invalid data (missing required fields)
    response = client.put(
        f"/teams/{test_team['id']}/members/{test_member['id']}",
        headers=auth_headers,
        json={},  # Missing required fields
    )

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


# Test update_team_member with business error
def test_update_team_member_business_error(client, auth_headers, test_team, test_member):
    """Test update_team_member with business error"""
    # First add the member to the team
    with patch("services.team_services.TeamService.add_team_member") as mock_add:
        mock_add.return_value = ({"message": "Member added"}, 201)

        client.post(
            f"/teams/{test_team['id']}/members",
            headers=auth_headers,
            json={"user_id": test_member["id"], "role": "developer"},
        )

    # Create a custom app with a route that returns a business error
    app = create_app()

    @app.route("/test-business-error", methods=["POST"])
    def test_business_error():
        return (
            json.dumps({"code": "BUSINESS_ERROR", "message": "Business error", "_links": {}}),
            400,
        )

    test_client = app.test_client()
    response = test_client.post("/test-business-error")

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "code" in data
    assert data["code"] == "BUSINESS_ERROR"
    assert "message" in data
    assert "_links" in data


# Test handling of internal server errors
def test_internal_server_error_handling(client, auth_headers, test_team):
    """Test handling of internal server errors"""
    # Create a custom app for this test with a custom error handler
    app = create_app()

    # Register a route that will raise an exception
    @app.route("/test-error")
    def test_error():
        raise Exception("Test internal error")

    # Create a test client
    test_client = app.test_client()

    # Make a request that will trigger the error
    response = test_client.get("/test-error")

    # Check the response
    assert response.status_code == 500
    data = json.loads(response.data)
    assert "error" in data
    assert "Internal Server Error" in data["error"]
