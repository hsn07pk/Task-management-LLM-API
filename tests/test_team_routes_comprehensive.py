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


# Test get_all_teams with different response formats
def test_get_all_teams_with_non_dict_teams(client, auth_headers):
    """Test get_all_teams with non-dictionary teams"""
    with patch("services.team_services.TeamService.get_all_teams") as mock_get_all_teams:
        mock_get_all_teams.return_value = ({"teams": ["Team1", "Team2"]}, 200)

        response = client.get("/teams/", headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert "Team1" in data
        assert "Team2" in data


# Test get_all_teams with error response
def test_get_all_teams_with_error(client, auth_headers):
    """Test get_all_teams with error response"""
    with patch("services.team_services.TeamService.get_all_teams") as mock_get_all_teams:
        mock_get_all_teams.return_value = ({"error": "Access denied"}, 403)

        response = client.get("/teams/", headers=auth_headers)

        assert response.status_code == 403
        data = json.loads(response.data)
        assert "error" in data
        assert data["error"] == "Access denied"


# Test get_team with different response formats
def test_get_team_with_string_response(client, auth_headers, test_team):
    """Test get_team with string response"""
    with patch("services.team_services.TeamService.get_team") as mock_get_team:
        mock_get_team.return_value = ("Team data", 200)

        response = client.get(f"/teams/{test_team['id']}", headers=auth_headers)

        assert response.status_code == 200
        data = response.data.decode("utf-8")
        assert "Team data" in data


# Test get_team with error response
def test_get_team_with_error(client, auth_headers, test_team):
    """Test get_team with error response"""
    with patch("services.team_services.TeamService.get_team") as mock_get_team:
        mock_get_team.return_value = ({"error": "Team not found"}, 404)

        response = client.get(f"/teams/{test_team['id']}", headers=auth_headers)

        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data
        assert data["error"] == "Team not found"


# Test update_team with different response formats
def test_update_team_with_string_response(client, auth_headers, test_team):
    """Test update_team with string response"""
    with patch("services.team_services.TeamService.update_team") as mock_update_team:
        mock_update_team.return_value = ("Team updated", 200)

        response = client.put(
            f"/teams/{test_team['id']}", headers=auth_headers, json={"name": "Updated Team Name"}
        )

        assert response.status_code == 200
        data = response.data.decode("utf-8")
        assert "Team updated" in data


# Test update_team with error response
def test_update_team_with_error(client, auth_headers, test_team):
    """Test update_team with error response"""
    with patch("services.team_services.TeamService.update_team") as mock_update_team:
        mock_update_team.return_value = ({"error": "Team not found"}, 404)

        response = client.put(
            f"/teams/{test_team['id']}", headers=auth_headers, json={"name": "Updated Team Name"}
        )

        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data
        assert data["error"] == "Team not found"


# Test delete_team with different response formats
def test_delete_team_with_string_response(client, auth_headers, test_team):
    """Test delete_team with string response"""
    with patch("services.team_services.TeamService.delete_team") as mock_delete_team:
        mock_delete_team.return_value = ("Team deleted", 200)

        response = client.delete(f"/teams/{test_team['id']}", headers=auth_headers)

        assert response.status_code == 200
        data = response.data.decode("utf-8")
        assert "Team deleted" in data


# Test delete_team with error response
def test_delete_team_with_error(client, auth_headers, test_team):
    """Test delete_team with error response"""
    with patch("services.team_services.TeamService.delete_team") as mock_delete_team:
        mock_delete_team.return_value = ({"error": "Team not found"}, 404)

        response = client.delete(f"/teams/{test_team['id']}", headers=auth_headers)

        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data
        assert data["error"] == "Team not found"


# Test get_team_members with different response formats
def test_get_team_members_non_dict_team(client, auth_headers, test_team):
    """Test get_team_members with non-dictionary team"""
    with patch("services.team_services.TeamService.get_team_members") as mock_get_members:
        mock_get_members.return_value = ({"team": "Team1", "members": []}, 200)

        response = client.get(f"/teams/{test_team['id']}/members", headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "team" in data
        assert data["team"] == "Team1"
        assert "members" in data
        assert "_links" in data


# Test get_team_members with non-list members
def test_get_team_members_non_list_members(client, auth_headers, test_team):
    """Test get_team_members with non-list members"""
    with patch("services.team_services.TeamService.get_team_members") as mock_get_members:
        mock_get_members.return_value = (
            {"team": {"id": test_team["id"]}, "members": "not a list"},
            200,
        )

        response = client.get(f"/teams/{test_team['id']}/members", headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "team" in data
        assert "members" in data
        assert "_links" in data


# Test get_team_members with error response
def test_get_team_members_with_error(client, auth_headers, test_team):
    """Test get_team_members with error response"""
    with patch("services.team_services.TeamService.get_team_members") as mock_get_members:
        mock_get_members.return_value = ({"error": "Team not found"}, 404)

        response = client.get(f"/teams/{test_team['id']}/members", headers=auth_headers)

        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data
        assert data["error"] == "Team not found"


# Test get_team_projects with different response formats
def test_get_team_projects_with_string_response(client, auth_headers, test_team):
    """Test get_team_projects with string response"""
    with patch("services.team_services.TeamService.get_team_projects") as mock_get_projects:
        mock_get_projects.return_value = ("Project data", 200)

        response = client.get(f"/teams/{test_team['id']}/projects", headers=auth_headers)

        assert response.status_code == 200
        data = response.data.decode("utf-8")
        assert "Project data" in data


# Test get_team_projects with error response
def test_get_team_projects_with_error(client, auth_headers, test_team):
    """Test get_team_projects with error response"""
    with patch("services.team_services.TeamService.get_team_projects") as mock_get_projects:
        mock_get_projects.return_value = ({"error": "Team not found"}, 404)

        response = client.get(f"/teams/{test_team['id']}/projects", headers=auth_headers)

        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data
        assert data["error"] == "Team not found"


# Test get_team_tasks with different response formats
def test_get_team_tasks_with_string_response(client, auth_headers, test_team):
    """Test get_team_tasks with string response"""
    with patch("services.team_services.TeamService.get_team_tasks") as mock_get_tasks:
        mock_get_tasks.return_value = ("Task data", 200)

        response = client.get(f"/teams/{test_team['id']}/tasks", headers=auth_headers)

        assert response.status_code == 200
        data = response.data.decode("utf-8")
        assert "Task data" in data


# Test get_team_tasks with error response
def test_get_team_tasks_with_error(client, auth_headers, test_team):
    """Test get_team_tasks with error response"""
    with patch("services.team_services.TeamService.get_team_tasks") as mock_get_tasks:
        mock_get_tasks.return_value = ({"error": "Team not found"}, 404)

        response = client.get(f"/teams/{test_team['id']}/tasks", headers=auth_headers)

        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data
        assert data["error"] == "Team not found"
