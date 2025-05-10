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
def test_add_team_member_with_validation_bypass(client, auth_headers, test_team, test_member):
    """Test add_team_member with valid data"""
    # Patch the service to return success
    with patch("services.team_services.TeamService.add_team_member") as mock_add_member:
        mock_add_member.return_value = ({"message": "Member added"}, 201)

        # Make the request with valid data that passes validation
        response = client.post(
            f"/teams/{test_team['id']}/members",
            headers=auth_headers,
            json={
                "user_id": test_member["id"],
                "role": "developer",  # Use a valid role from the enum
            },
        )

        # Check the response
        assert response.status_code == 201
        data = json.loads(response.data)
        assert "message" in data


# Test update_team_member with valid data
def test_update_team_member_with_validation_bypass(client, auth_headers, test_team, test_member):
    """Test update_team_member with valid data"""
    # First add the member to the team
    with patch("services.team_services.TeamService.add_team_member") as mock_add:
        mock_add.return_value = ({"message": "Member added"}, 201)

        client.post(
            f"/teams/{test_team['id']}/members",
            headers=auth_headers,
            json={
                "user_id": test_member["id"],
                "role": "developer",  # Use a valid role from the enum
            },
        )

    # Now test update with valid data
    with patch("services.team_services.TeamService.update_team_member") as mock_update_member:
        mock_update_member.return_value = ({"message": "Role updated"}, 200)

        # Make the request with valid data that passes validation
        response = client.put(
            f"/teams/{test_team['id']}/members/{test_member['id']}",
            headers=auth_headers,
            json={
                "user_id": test_member["id"],  # Include user_id as required by schema
                "role": "tester",  # Use a valid role from the enum
            },
        )

        # Check the response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "message" in data
