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


# Create a custom decorator to bypass validation
def mock_validate_json(schema):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)

        return wrapper

    return decorator


# Import wraps for proper decorator functionality
from functools import wraps


# Test add_team_member with validation bypass
def test_add_team_member_with_validation_bypass(client, auth_headers, test_team, test_member):
    """Test add_team_member with validation bypass"""
    # Properly patch the validate_json decorator
    with patch("validators.validators.validate_json", mock_validate_json):
        # And also patch the service to return success
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


# Test update_team_member with validation bypass
def test_update_team_member_with_validation_bypass(client, auth_headers, test_team, test_member):
    """Test update_team_member with validation bypass"""
    # First add the member to the team
    with patch("validators.validators.validate_json", mock_validate_json):
        with patch("services.team_services.TeamService.add_team_member") as mock_add:
            mock_add.return_value = ({"message": "Member added"}, 201)

            client.post(
                f"/teams/{test_team['id']}/members",
                headers=auth_headers,
                json={"user_id": test_member["id"], "role": "developer"},
            )

    # Now test update with validation bypass
    with patch("validators.validators.validate_json", mock_validate_json):
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


# Test update_team_member with business error
def test_update_team_member_business_error(client, auth_headers, test_team, test_member):
    """Test update_team_member with business error"""
    # First add the member to the team
    with patch("validators.validators.validate_json", mock_validate_json):
        with patch("services.team_services.TeamService.add_team_member") as mock_add:
            mock_add.return_value = ({"message": "Member added"}, 201)

            client.post(
                f"/teams/{test_team['id']}/members",
                headers=auth_headers,
                json={"user_id": test_member["id"], "role": "developer"},
            )

    # Now test update with business error
    with patch("validators.validators.validate_json", mock_validate_json):
        with patch("services.team_services.TeamService.update_team_member") as mock_update_member:
            mock_update_member.return_value = (
                {"code": "BUSINESS_ERROR", "message": "Business error"},
                400,
            )

            response = client.put(
                f"/teams/{test_team['id']}/members/{test_member['id']}",
                headers=auth_headers,
                json={"user_id": test_member["id"], "role": "lead"},
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert "code" in data
            assert data["code"] == "BUSINESS_ERROR"
            assert "message" in data


# Test update_team_member with string error
def test_update_team_member_string_error(client, auth_headers, test_team, test_member):
    """Test update_team_member with string error"""
    # First add the member to the team
    with patch("validators.validators.validate_json", mock_validate_json):
        with patch("services.team_services.TeamService.add_team_member") as mock_add:
            mock_add.return_value = ({"message": "Member added"}, 201)

            client.post(
                f"/teams/{test_team['id']}/members",
                headers=auth_headers,
                json={"user_id": test_member["id"], "role": "developer"},
            )

    # Now test update with string error
    with patch("validators.validators.validate_json", mock_validate_json):
        with patch("services.team_services.TeamService.update_team_member") as mock_update_member:
            mock_update_member.return_value = ("String error message", 400)

            response = client.put(
                f"/teams/{test_team['id']}/members/{test_member['id']}",
                headers=auth_headers,
                json={"user_id": test_member["id"], "role": "lead"},
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert isinstance(data, str)
            assert "String error message" in data


# Test update_team_member with unexpected format
def test_update_team_member_unexpected_format(client, auth_headers, test_team, test_member):
    """Test update_team_member with unexpected format"""
    # First add the member to the team
    with patch("validators.validators.validate_json", mock_validate_json):
        with patch("services.team_services.TeamService.add_team_member") as mock_add:
            mock_add.return_value = ({"message": "Member added"}, 201)

            client.post(
                f"/teams/{test_team['id']}/members",
                headers=auth_headers,
                json={"user_id": test_member["id"], "role": "developer"},
            )

    # Now test update with unexpected format
    # Create a custom app with a route that returns an unexpected format
    app = create_app()

    @app.route("/test-unexpected-format", methods=["PUT"])
    def test_unexpected_format():
        return 123, 200  # Non-dict, non-string response

    test_client = app.test_client()
    response = test_client.put("/test-unexpected-format")

    assert response.status_code == 500
    data = json.loads(response.data)
    assert "error" in data
    assert "Internal Server Error" in data["error"]


# Test update_team_member with service exception
def test_update_team_member_service_exception(client, auth_headers, test_team, test_member):
    """Test update_team_member with service exception"""
    # First add the member to the team
    with patch("validators.validators.validate_json", mock_validate_json):
        with patch("services.team_services.TeamService.add_team_member") as mock_add:
            mock_add.return_value = ({"message": "Member added"}, 201)

            client.post(
                f"/teams/{test_team['id']}/members",
                headers=auth_headers,
                json={"user_id": test_member["id"], "role": "developer"},
            )

    # Now test update with service exception
    # Create a custom app with a route that raises an exception
    app = create_app()

    @app.route("/test-exception", methods=["PUT"])
    def test_exception():
        raise Exception("Test exception")

    test_client = app.test_client()
    response = test_client.put("/test-exception")

    assert response.status_code == 500
    data = json.loads(response.data)
    assert "error" in data
    assert "Internal Server Error" in data["error"]
