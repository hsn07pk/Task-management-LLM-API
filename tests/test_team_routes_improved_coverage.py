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


# Test get_team_projects with error response
def test_get_team_projects_error_response(client, auth_headers, test_team):
    """Test get_team_projects with error response"""
    with patch("services.team_services.TeamService.get_team_projects") as mock_get_projects:
        mock_get_projects.return_value = ({"error": "Not authorized"}, 403)

        response = client.get(f"/teams/{test_team['id']}/projects", headers=auth_headers)

        assert response.status_code == 403
        data = json.loads(response.data)
        assert "error" in data
        assert "_links" in data


# Test get_team_tasks with different response formats
def test_get_team_tasks_non_dict_response(client, auth_headers, test_team):
    """Test get_team_tasks with non-dictionary response"""
    with patch("services.team_services.TeamService.get_team_tasks") as mock_get_tasks:
        mock_get_tasks.return_value = ("String response", 200)

        response = client.get(f"/teams/{test_team['id']}/tasks", headers=auth_headers)

        assert response.status_code == 200
        data = response.data.decode("utf-8")
        assert "String response" in data


# Test error handling in get_team_members
def test_get_team_members_error_handling(client, auth_headers, test_team):
    """Test error handling in get_team_members"""
    with patch("services.team_services.TeamService.get_team_members") as mock_get_members:
        # Test with a non-dict team and non-list members
        mock_get_members.return_value = ({"team": "Team1", "members": "not a list"}, 200)

        response = client.get(f"/teams/{test_team['id']}/members", headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "team" in data
        assert "members" in data
        assert "_links" in data


# Test error handling in get_team
def test_get_team_error_handling(client, auth_headers, test_team):
    """Test error handling in get_team"""
    with patch("services.team_services.TeamService.get_team") as mock_get_team:
        # Test with a non-dict team
        mock_get_team.return_value = ("Team not found", 404)

        response = client.get(f"/teams/{test_team['id']}", headers=auth_headers)

        assert response.status_code == 404
        data = json.loads(response.data)
        assert isinstance(data, str) or "message" in data


# Test error handling in update_team
def test_update_team_error_handling(client, auth_headers, test_team):
    """Test error handling in update_team"""
    with patch("services.team_services.TeamService.update_team") as mock_update_team:
        # Test with a non-dict response
        mock_update_team.return_value = ("Team updated", 200)

        response = client.put(
            f"/teams/{test_team['id']}", headers=auth_headers, json={"name": "Updated Team Name"}
        )

        assert response.status_code == 200
        data = response.data.decode("utf-8")
        assert "Team updated" in data


# Test error handling in delete_team
def test_delete_team_error_handling(client, auth_headers, test_team):
    """Test error handling in delete_team"""
    with patch("services.team_services.TeamService.delete_team") as mock_delete_team:
        # Test with a non-dict response
        mock_delete_team.return_value = ("Team deleted", 200)

        response = client.delete(f"/teams/{test_team['id']}", headers=auth_headers)

        assert response.status_code == 200
        data = response.data.decode("utf-8")
        assert "Team deleted" in data


# Test error handling in add_team_member
def test_add_team_member_error_handling(client, auth_headers, test_team, test_member):
    """Test error handling in add_team_member"""
    with patch("services.team_services.TeamService.add_team_member") as mock_add_member:
        # Test with a non-dict response
        mock_add_member.return_value = ("Member added", 201)

        response = client.post(
            f"/teams/{test_team['id']}/members",
            headers=auth_headers,
            json={"user_id": test_member["id"], "role": "developer"},
        )

        assert response.status_code == 201
        data = response.data.decode("utf-8")
        assert "Member added" in data


# Test error handling in get_team_member
def test_get_team_member_error_handling(client, auth_headers, test_team, test_member):
    """Test error handling in get_team_member"""
    with patch("services.team_services.TeamService.get_team_member") as mock_get_member:
        # Test with a non-dict response
        mock_get_member.return_value = ("Member not found", 404)

        response = client.get(
            f"/teams/{test_team['id']}/members/{test_member['id']}", headers=auth_headers
        )

        assert response.status_code == 404
        data = response.data.decode("utf-8")
        assert "Member not found" in data


# Test error handling in update_team_member
def test_update_team_member_error_handling(client, auth_headers, test_team, test_member):
    """Test error handling in update_team_member"""
    # First add the member to the team
    add_response = client.post(
        f"/teams/{test_team['id']}/members",
        headers=auth_headers,
        json={"user_id": test_member["id"], "role": "member"},
    )

    with patch("services.team_services.TeamService.update_team_member") as mock_update_member:
        # Test with a non-dict response
        mock_update_member.return_value = ("Role updated", 200)

        response = client.put(
            f"/teams/{test_team['id']}/members/{test_member['id']}",
            headers=auth_headers,
            json={"user_id": test_member["id"], "role": "lead"},
        )

        assert response.status_code == 200
        data = response.data.decode("utf-8")
        assert "Role updated" in data


# Test error handling in remove_team_member
def test_remove_team_member_error_handling(client, auth_headers, test_team, test_member):
    """Test error handling in remove_team_member"""
    # First add the member to the team
    add_response = client.post(
        f"/teams/{test_team['id']}/members",
        headers=auth_headers,
        json={"user_id": test_member["id"], "role": "member"},
    )

    with patch("services.team_services.TeamService.remove_team_member") as mock_remove_member:
        # Test with a non-dict response
        mock_remove_member.return_value = ("Member removed", 200)

        response = client.delete(
            f"/teams/{test_team['id']}/members/{test_member['id']}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.data.decode("utf-8")
        assert "Member removed" in data
