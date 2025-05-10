import json
import os
import uuid
from unittest.mock import MagicMock, patch

import pytest
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash

from app import create_app
from models import Project, Task, Team, TeamMembership, User, db

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


# Test get_all_teams with non-dictionary teams
def test_get_all_teams_with_non_dict_teams(client, auth_headers):
    """Test get_all_teams when the response contains non-dictionary teams"""
    with patch("services.team_services.TeamService.get_all_teams") as mock_get_all_teams:
        # Return a response with teams as strings instead of dictionaries
        mock_get_all_teams.return_value = ({"teams": ["Team1", "Team2"]}, 200)

        response = client.get("/teams/", headers=auth_headers)

        # Check response
        assert response.status_code == 200
        data = json.loads(response.data)

        # Verify the response contains the raw teams
        assert isinstance(data, list)
        assert "Team1" in data
        assert "Team2" in data


# Test get_team_members with non-dictionary team
def test_get_team_members_non_dict_team(client, auth_headers, test_team):
    """Test get_team_members when the team in the response is not a dictionary"""
    with patch("services.team_services.TeamService.get_team_members") as mock_get_members:
        # Return a response with team as a string instead of a dictionary
        mock_get_members.return_value = ({"team": "Team1", "members": []}, 200)

        response = client.get(f"/teams/{test_team['id']}/members", headers=auth_headers)

        # Check response
        assert response.status_code == 200
        data = json.loads(response.data)

        # Verify the response structure
        assert "team" in data
        assert data["team"] == "Team1"
        assert "members" in data
        assert "_links" in data


# Test get_team_projects with error response
def test_get_team_projects_error_response(client, auth_headers, test_team):
    """Test get_team_projects when the service returns an error"""
    with patch("services.team_services.TeamService.get_team_projects") as mock_get_projects:
        # Return an error response
        mock_get_projects.return_value = ({"error": "Not authorized"}, 403)

        response = client.get(f"/teams/{test_team['id']}/projects", headers=auth_headers)

        # Check response
        assert response.status_code == 403
        data = json.loads(response.data)

        # Verify error structure
        assert "error" in data
        assert "_links" in data


# Test get_team_tasks with non-dictionary response
def test_get_team_tasks_non_dict_response(client, auth_headers, test_team):
    """Test get_team_tasks when the service returns a non-dictionary response"""
    with patch("services.team_services.TeamService.get_team_tasks") as mock_get_tasks:
        # Return a string response
        mock_get_tasks.return_value = ("String response", 200)

        response = client.get(f"/teams/{test_team['id']}/tasks", headers=auth_headers)

        # Check response
        assert response.status_code == 200

        # Check that the response contains the string
        data = response.data.decode("utf-8")
        assert "String response" in data


# Test error handling in get_team_members
def test_get_team_members_non_list_members(client, auth_headers, test_team):
    """Test get_team_members when the members in the response is not a list"""
    with patch("services.team_services.TeamService.get_team_members") as mock_get_members:
        # Return a response with members as a string instead of a list
        mock_get_members.return_value = (
            {"team": {"id": test_team["id"]}, "members": "not a list"},
            200,
        )

        response = client.get(f"/teams/{test_team['id']}/members", headers=auth_headers)

        # Check response
        assert response.status_code == 200
        data = json.loads(response.data)

        # Verify the response structure
        assert "team" in data
        assert "members" in data
        assert "_links" in data
