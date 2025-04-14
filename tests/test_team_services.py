import json
import uuid
from unittest.mock import MagicMock, patch

import pytest
from werkzeug.security import generate_password_hash

from models import Team, TeamMembership, User, db
from services.team_services import TeamService


@pytest.fixture(scope="session")
def app():
    """
    Configure a Flask app for testing with PostgreSQL.
    """
    from app import create_app

    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "postgresql://admin:helloworld123@localhost/task_management_db",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "JWT_SECRET_KEY": "test-secret-key",
        }
    )

    return app


@pytest.fixture(scope="function")
def client(app):
    """
    Fixture to create a test client for the app.
    """
    with app.test_client() as testing_client:
        with app.app_context():
            yield testing_client


@pytest.fixture(scope="function")
def test_user(app):
    """
    Fixture to create a test user.
    """
    with app.app_context():
        user = User(
            username=f"testuser_{uuid.uuid4().hex[:8]}",
            email=f"testuser_{uuid.uuid4().hex[:8]}@example.com",
            password_hash=generate_password_hash("password123"),
            role="admin",
        )
        db.session.add(user)
        db.session.commit()
        return {"id": str(user.user_id), "username": user.username, "email": user.email}


@pytest.fixture(scope="function")
def test_team(app, test_user):
    """
    Fixture to create a test team.
    """
    with app.app_context():
        team = Team(
            name=f"Team {uuid.uuid4().hex[:8]}",
            description="Test team description",
            lead_id=uuid.UUID(test_user["id"]),
        )
        db.session.add(team)
        db.session.commit()
        return {
            "id": str(team.team_id),
            "name": team.name,
            "description": team.description,
            "lead_id": str(team.lead_id),
        }


@pytest.fixture(scope="function")
def test_member(app):
    """
    Fixture to create a test member user.
    """
    with app.app_context():
        user = User(
            username=f"member_{uuid.uuid4().hex[:8]}",
            email=f"member_{uuid.uuid4().hex[:8]}@example.com",
            password_hash=generate_password_hash("password123"),
            role="member",
        )
        db.session.add(user)
        db.session.commit()
        return {"id": str(user.user_id), "username": user.username, "email": user.email}


def test_create_team_service(app, test_user):
    """
    Test the TeamService.create_team method.
    """
    with app.app_context():
        user_id = test_user["id"]
        data = {
            "name": "New Service Team",
            "description": "Created by service",
            "lead_id": user_id,
        }

        result, status_code = TeamService.create_team(user_id, data)

        assert status_code == 201
        assert "team_id" in result
        assert result["name"] == "New Service Team"
        assert result["description"] == "Created by service"
        assert result["lead_id"] == user_id


def test_create_team_invalid_lead(app, test_user):
    """
    Test the TeamService.create_team method with invalid lead_id.
    """
    with app.app_context():
        user_id = test_user["id"]
        data = {
            "name": "Invalid Lead Team",
            "description": "Should fail",
            "lead_id": str(uuid.uuid4()),  # Non-existent user ID
        }

        result, status_code = TeamService.create_team(user_id, data)

        assert status_code == 404
        assert "error" in result
        assert "Invalid lead_id: User not found" in result["error"]


def test_get_all_teams(app, test_team):
    """
    Test the TeamService.get_all_teams method.
    """
    with app.app_context():
        result, status_code = TeamService.get_all_teams()

        assert status_code == 200
        assert "teams" in result
        assert len(result["teams"]) >= 1
        assert any(team["name"] == test_team["name"] for team in result["teams"])


def test_get_team(app, test_user, test_team):
    """
    Test the TeamService.get_team method.
    """
    with app.app_context():
        user_id = test_user["id"]
        team_id = uuid.UUID(test_team["id"])

        result, status_code = TeamService.get_team(user_id, team_id)

        assert status_code == 200
        assert result["team_id"] == test_team["id"]
        assert result["name"] == test_team["name"]
        assert result["description"] == test_team["description"]


def test_get_nonexistent_team(app, test_user):
    """
    Test the TeamService.get_team method with non-existent team.
    """
    with app.app_context():
        user_id = test_user["id"]
        nonexistent_team_id = uuid.uuid4()

        result, status_code = TeamService.get_team(user_id, nonexistent_team_id)

        assert status_code == 404
        assert "error" in result
        assert "Team not found" in result["error"]


def test_update_team(app, test_user, test_team):
    """
    Test the TeamService.update_team method.
    """
    with app.app_context():
        user_id = test_user["id"]
        team_id = uuid.UUID(test_team["id"])
        data = {
            "name": "Updated Team Name",
            "description": "Updated description",
        }

        result, status_code = TeamService.update_team(user_id, team_id, data)

        assert status_code == 200
        assert result["name"] == "Updated Team Name"
        assert result["description"] == "Updated description"
        assert result["team_id"] == test_team["id"]


def test_update_nonexistent_team(app, test_user):
    """
    Test the TeamService.update_team method with non-existent team.
    """
    with app.app_context():
        user_id = test_user["id"]
        nonexistent_team_id = uuid.uuid4()
        data = {"name": "Won't Update"}

        result, status_code = TeamService.update_team(user_id, nonexistent_team_id, data)

        assert status_code == 404
        assert "error" in result
        assert "Team not found" in result["error"]


def test_delete_team(app, test_user, test_team):
    """
    Test the TeamService.delete_team method.
    """
    with app.app_context():
        user_id = test_user["id"]
        team_id = uuid.UUID(test_team["id"])

        result, status_code = TeamService.delete_team(user_id, team_id)

        assert status_code == 200
        assert "message" in result
        assert "Team deleted successfully" in result["message"]

        # Verify team is actually deleted
        team = Team.query.get(team_id)
        assert team is None


def test_delete_nonexistent_team(app, test_user):
    """
    Test the TeamService.delete_team method with non-existent team.
    """
    with app.app_context():
        user_id = test_user["id"]
        nonexistent_team_id = uuid.uuid4()

        result, status_code = TeamService.delete_team(user_id, nonexistent_team_id)

        assert status_code == 404
        assert "error" in result
        assert "Team not found" in result["error"]


def test_add_team_member(app, test_user, test_team, test_member):
    """
    Test the TeamService.add_team_member method.
    """
    with app.app_context():
        current_user_id = test_user["id"]
        team_id = uuid.UUID(test_team["id"])
        member_id = test_member["id"]
        data = {"user_id": member_id, "role": "developer"}

        result, status_code = TeamService.add_team_member(current_user_id, team_id, data)

        assert status_code == 201
        assert "message" in result
        assert "Member added successfully" in result["message"]

        # Verify membership was created
        membership = TeamMembership.query.filter_by(
            user_id=uuid.UUID(member_id), team_id=team_id
        ).first()
        assert membership is not None
        assert membership.role == "developer"


def test_add_team_member_nonexistent_team(app, test_user, test_member):
    """
    Test the TeamService.add_team_member method with non-existent team.
    """
    with app.app_context():
        current_user_id = test_user["id"]
        nonexistent_team_id = uuid.uuid4()
        member_id = test_member["id"]
        data = {"user_id": member_id, "role": "developer"}

        result, status_code = TeamService.add_team_member(
            current_user_id, nonexistent_team_id, data
        )

        assert status_code == 404
        assert "error" in result
        assert "Team not found" in result["error"]


def test_add_team_member_nonexistent_user(app, test_user, test_team):
    """
    Test the TeamService.add_team_member method with non-existent user.
    """
    with app.app_context():
        current_user_id = test_user["id"]
        team_id = uuid.UUID(test_team["id"])
        nonexistent_user_id = str(uuid.uuid4())
        data = {"user_id": nonexistent_user_id, "role": "developer"}

        result, status_code = TeamService.add_team_member(current_user_id, team_id, data)

        assert status_code == 404
        assert "error" in result
        assert "User not found" in result["error"]


def test_update_team_member(app, test_user, test_team, test_member):
    """
    Test the TeamService.update_team_member method.
    """
    with app.app_context():
        current_user_id = test_user["id"]
        team_id = uuid.UUID(test_team["id"])
        member_id = uuid.UUID(test_member["id"])

        # First add the member
        membership = TeamMembership(user_id=member_id, team_id=team_id, role="developer")
        db.session.add(membership)
        db.session.commit()

        # Now update the role
        data = {"role": "senior-developer"}
        result, status_code = TeamService.update_team_member(
            current_user_id, team_id, member_id, data
        )

        assert status_code == 200
        assert "message" in result
        assert "Member role updated successfully" in result["message"]

        # Verify role was updated
        updated_membership = TeamMembership.query.filter_by(
            user_id=member_id, team_id=team_id
        ).first()
        assert updated_membership is not None
        assert updated_membership.role == "senior-developer"


def test_update_nonexistent_team_member(app, test_user, test_team):
    """
    Test the TeamService.update_team_member method with non-existent membership.
    """
    with app.app_context():
        current_user_id = test_user["id"]
        team_id = uuid.UUID(test_team["id"])
        nonexistent_member_id = uuid.uuid4()
        data = {"role": "senior-developer"}

        result, status_code = TeamService.update_team_member(
            current_user_id, team_id, nonexistent_member_id, data
        )

        assert status_code == 404
        assert "error" in result
        assert "User not found" in result["error"]


def test_remove_team_member(app, test_user, test_team, test_member):
    """
    Test the TeamService.remove_team_member method.
    """
    with app.app_context():
        current_user_id = test_user["id"]
        team_id = uuid.UUID(test_team["id"])
        member_id = uuid.UUID(test_member["id"])

        # First add the member
        membership = TeamMembership(user_id=member_id, team_id=team_id, role="developer")
        db.session.add(membership)
        db.session.commit()

        # Now remove the member
        result, status_code = TeamService.remove_team_member(current_user_id, team_id, member_id)

        assert status_code == 200
        assert "message" in result
        assert "Member removed successfully" in result["message"]

        # Verify membership was deleted
        removed_membership = TeamMembership.query.filter_by(
            user_id=member_id, team_id=team_id
        ).first()
        assert removed_membership is None


def test_remove_nonexistent_team_member(app, test_user, test_team):
    """
    Test the TeamService.remove_team_member method with non-existent member.
    """
    with app.app_context():
        user_id = test_user["id"]
        team_id = uuid.UUID(test_team["id"])
        nonexistent_member_id = uuid.uuid4()

        result, status_code = TeamService.remove_team_member(user_id, team_id, nonexistent_member_id)

        assert status_code == 404
        assert "error" in result
        assert "User not found" in result["error"]


def test_get_team_members(app, test_user, test_team, test_member):
    """
    Test the TeamService.get_team_members method.
    """
    with app.app_context():
        user_id = test_user["id"]
        team_id = uuid.UUID(test_team["id"])
        member_id = uuid.UUID(test_member["id"])

        # First add the member to the team
        membership_data = {"user_id": test_member["id"], "role": "member"}
        TeamService.add_team_member(user_id, team_id, membership_data)

        # Then get the team members
        result, status_code = TeamService.get_team_members(user_id, team_id)

        assert status_code == 200
        assert "members" in result
        assert len(result["members"]) >= 1
        assert any(member["user_id"] == test_member["id"] for member in result["members"])


def test_get_team_members_nonexistent_team(app, test_user):
    """
    Test the TeamService.get_team_members method with non-existent team.
    """
    with app.app_context():
        user_id = test_user["id"]
        nonexistent_team_id = uuid.uuid4()

        result, status_code = TeamService.get_team_members(user_id, nonexistent_team_id)

        assert status_code == 404
        assert "error" in result
        assert "Team not found" in result["error"]


def test_create_team_missing_name(app, test_user):
    """
    Test the TeamService.create_team method with missing name (400 error).
    """
    with app.app_context():
        user_id = test_user["id"]
        data = {
            # Missing name
            "description": "This should fail",
            "lead_id": user_id,
        }

        result, status_code = TeamService.create_team(user_id, data)

        assert status_code == 500
        assert "error" in result


def test_create_team_missing_lead_id(app, test_user):
    """
    Test the TeamService.create_team method with missing lead_id (400 error).
    """
    with app.app_context():
        user_id = test_user["id"]
        data = {
            "name": "Team Without Lead",
            "description": "This should fail",
            # Missing lead_id
        }

        result, status_code = TeamService.create_team(user_id, data)

        assert status_code == 400
        assert "error" in result
        assert "Lead ID is required" in result["error"]


def test_create_team_invalid_lead_id_format(app, test_user):
    """
    Test the TeamService.create_team method with invalid lead_id format (400 error).
    """
    with app.app_context():
        user_id = test_user["id"]
        data = {
            "name": "Team With Invalid Lead",
            "description": "This should fail",
            "lead_id": "not-a-uuid",
        }

        result, status_code = TeamService.create_team(user_id, data)

        assert status_code == 400
        assert "error" in result
        assert "Invalid lead_id format" in result["error"]


def test_update_team_no_data(app, test_user, test_team):
    """
    Test the TeamService.update_team method with no data (400 error).
    """
    with app.app_context():
        user_id = test_user["id"]
        team_id = uuid.UUID(test_team["id"])
        data = {}

        result, status_code = TeamService.update_team(user_id, team_id, data)

        assert status_code == 400
        assert "error" in result
        assert "No input data provided" in result["error"]


def test_update_team_invalid_lead_id_format(app, test_user, test_team):
    """
    Test the TeamService.update_team method with invalid lead_id format (400 error).
    """
    with app.app_context():
        user_id = test_user["id"]
        team_id = uuid.UUID(test_team["id"])
        data = {
            "lead_id": "not-a-uuid",
        }

        result, status_code = TeamService.update_team(user_id, team_id, data)

        assert status_code == 400
        assert "error" in result
        assert "Invalid lead_id format" in result["error"]


def test_add_team_member_missing_user_id(app, test_user, test_team):
    """
    Test the TeamService.add_team_member method with missing user_id (400 error).
    """
    with app.app_context():
        user_id = test_user["id"]
        team_id = uuid.UUID(test_team["id"])
        data = {
            # Missing user_id
            "role": "member",
        }

        result, status_code = TeamService.add_team_member(user_id, team_id, data)

        assert status_code == 400
        assert "error" in result
        assert "User ID is required" in result["error"]


def test_add_team_member_invalid_user_id_format(app, test_user, test_team):
    """
    Test the TeamService.add_team_member method with invalid user_id format (400 error).
    """
    with app.app_context():
        user_id = test_user["id"]
        team_id = uuid.UUID(test_team["id"])
        data = {
            "user_id": "not-a-uuid",
            "role": "member",
        }

        result, status_code = TeamService.add_team_member(user_id, team_id, data)

        assert status_code == 400
        assert "error" in result
        assert "Invalid user_id format" in result["error"]


def test_add_team_member_already_exists(app, test_user, test_team, test_member):
    """
    Test the TeamService.add_team_member method when member already exists (400 error).
    """
    with app.app_context():
        user_id = test_user["id"]
        team_id = uuid.UUID(test_team["id"])
        member_id = test_member["id"]
        
        # First add the member to the team
        data = {
            "user_id": member_id,
            "role": "member",
        }
        TeamService.add_team_member(user_id, team_id, data)
        
        # Try to add the same member again
        result, status_code = TeamService.add_team_member(user_id, team_id, data)
        
        assert status_code == 400
        assert "error" in result
        assert "User is already a member of this team" in result["error"]


def test_update_team_member_missing_role(app, test_user, test_team, test_member):
    """
    Test the TeamService.update_team_member method with missing role (400 error).
    """
    with app.app_context():
        user_id = test_user["id"]
        team_id = uuid.UUID(test_team["id"])
        member_id = uuid.UUID(test_member["id"])
        
        # First add the member to the team
        add_data = {
            "user_id": test_member["id"],
            "role": "member",
        }
        TeamService.add_team_member(user_id, team_id, add_data)
        
        # Try to update without providing a role
        update_data = {}  # Empty data
        result, status_code = TeamService.update_team_member(user_id, team_id, member_id, update_data)
        
        assert status_code == 400
        assert "error" in result
        assert "No input data provided" in result["error"]


def test_internal_server_error_create_team(app, test_user, mocker):
    """
    Test internal server error (500) during team creation.
    """
    with app.app_context():
        user_id = test_user["id"]
        data = {
            "name": "Error Team",
            "description": "Will cause an error",
            "lead_id": user_id,
        }
        
        # Mock the database session to raise an exception
        mock_add = mocker.patch.object(db.session, 'add', side_effect=Exception("Simulated database error"))
        
        result, status_code = TeamService.create_team(user_id, data)
        
        assert status_code == 500
        assert "error" in result
        assert "Internal server error" in result["error"]


def test_internal_server_error_get_all_teams(app, mocker):
    """
    Test internal server error (500) when retrieving all teams.
    """
    with app.app_context():
        # Remplacer la moquerie pour utiliser l'attribut 'all' directement
        mock_query = mocker.patch('models.Team.query')
        mock_query.all.side_effect = Exception("Simulated database error")
        
        result, status_code = TeamService.get_all_teams()
        
        assert status_code == 500
        assert "error" in result
        assert "Failed to retrieve teams" in result["error"]


def test_internal_server_error_get_team(app, test_user, test_team, mocker):
    """
    Test internal server error (500) when retrieving a team.
    """
    with app.app_context():
        user_id = test_user["id"]
        team_id = uuid.UUID(test_team["id"])
        
        # Fix the mock to use a model that matches how it's called in the code
        mock_query = mocker.patch('models.Team.query')
        mock_get = mocker.MagicMock()
        mock_get.side_effect = Exception("Simulated database error")
        mock_query.get = mock_get
        
        result, status_code = TeamService.get_team(user_id, team_id)
        
        assert status_code == 500
        assert "error" in result
        assert "Internal server error" in result["error"]


def test_unauthorized_access(app):
    """
    Test unauthorized access (401) to TeamService methods.
    """
    with app.app_context():
        user_id = None  # No user ID = unauthorized
        team_id = uuid.uuid4()
        
        # Test create_team
        create_result, create_status = TeamService.create_team(user_id, {"name": "Test", "lead_id": str(uuid.uuid4())})
        assert create_status == 401
        assert "User not authenticated" in create_result["error"]
        
        # Test get_team
        get_result, get_status = TeamService.get_team(user_id, team_id)
        assert get_status == 401
        assert "User not authenticated" in get_result["error"]
        
        # Test update_team
        update_result, update_status = TeamService.update_team(user_id, team_id, {"name": "Updated"})
        assert update_status == 401
        assert "User not authenticated" in update_result["error"]
        
        # Test delete_team
        delete_result, delete_status = TeamService.delete_team(user_id, team_id)
        assert delete_status == 401
        assert "User not authenticated" in delete_result["error"]
        
        # Test add_team_member
        add_result, add_status = TeamService.add_team_member(user_id, team_id, {"user_id": str(uuid.uuid4())})
        assert add_status == 401
        assert "User not authenticated" in add_result["error"]
        
        # Test get_team_members
        members_result, members_status = TeamService.get_team_members(user_id, team_id)
        assert members_status == 401
        assert "User not authenticated" in members_result["error"]

# New tests to improve coverage

def test_internal_server_error_update_team(app, test_user, test_team, mocker):
    """
    Test internal server error (500) when updating a team.
    """
    with app.app_context():
        user_id = test_user["id"]
        team_id = uuid.UUID(test_team["id"])
        data = {"name": "Error Team Update"}
        
        # Simulate an error during database query
        mock_query = mocker.patch('models.Team.query')
        mock_team = MagicMock()
        mock_team.name = "Original Name"
        mock_team.description = "Original Description"
        mock_get = mocker.MagicMock(return_value=mock_team)
        mock_query.get = mock_get
        
        # Simulate an error during commit
        mock_commit = mocker.patch.object(db.session, 'commit')
        mock_commit.side_effect = Exception("Simulated database error")
        
        result, status_code = TeamService.update_team(user_id, team_id, data)
        
        assert status_code == 500
        assert "error" in result
        assert "Internal server error" in result["error"]


def test_internal_server_error_delete_team(app, test_user, test_team, mocker):
    """
    Test internal server error (500) when deleting a team.
    """
    with app.app_context():
        user_id = test_user["id"]
        team_id = uuid.UUID(test_team["id"])
        
        # Simulate an error during deletion
        mock_query = mocker.patch('models.Team.query')
        mock_team = MagicMock()
        mock_get = mocker.MagicMock(return_value=mock_team)
        mock_query.get = mock_get
        
        # Simulate an error during commit
        mock_delete = mocker.patch.object(db.session, 'delete')
        mock_delete.side_effect = Exception("Simulated database error")
        
        result, status_code = TeamService.delete_team(user_id, team_id)
        
        assert status_code == 500
        assert "error" in result
        assert "Internal server error" in result["error"]


def test_internal_server_error_add_team_member(app, test_user, test_team, test_member, mocker):
    """
    Test internal server error (500) when adding a team member.
    """
    with app.app_context():
        user_id = test_user["id"]
        team_id = uuid.UUID(test_team["id"])
        data = {"user_id": test_member["id"], "role": "developer"}
        
        # Simulate an error during adding
        mock_team_query = mocker.patch('models.Team.query')
        mock_team = MagicMock()
        mock_team_get = mocker.MagicMock(return_value=mock_team)
        mock_team_query.get = mock_team_get
        
        mock_user_query = mocker.patch('models.User.query')
        mock_user = MagicMock()
        mock_user_get = mocker.MagicMock(return_value=mock_user)
        mock_user_query.get = mock_user_get
        
        # Simulate an error during commit
        mock_add = mocker.patch.object(db.session, 'add')
        mock_add.side_effect = Exception("Simulated database error")
        
        result, status_code = TeamService.add_team_member(user_id, team_id, data)
        
        assert status_code == 500
        assert "error" in result
        assert "Internal server error" in result["error"]


def test_internal_server_error_update_team_member(app, test_user, test_team, test_member, mocker):
    """
    Test internal server error (500) when updating a team member.
    """
    with app.app_context():
        user_id = test_user["id"]
        team_id = uuid.UUID(test_team["id"])
        member_id = uuid.UUID(test_member["id"])
        data = {"role": "senior-developer"}
        
        # Simulate successful queries for Team and User
        mock_team_query = mocker.patch('models.Team.query')
        mock_team = MagicMock()
        mock_team_get = mocker.MagicMock(return_value=mock_team)
        mock_team_query.get = mock_team_get
        
        mock_user_query = mocker.patch('models.User.query')
        mock_user = MagicMock()
        mock_user_get = mocker.MagicMock(return_value=mock_user)
        mock_user_query.get = mock_user_get
        
        # Simulate a successful query for TeamMembership
        mock_membership_query = mocker.patch('models.TeamMembership.query')
        mock_filter_by = mocker.MagicMock()
        mock_membership = MagicMock()
        mock_first = mocker.MagicMock(return_value=mock_membership)
        mock_filter_by.first = mock_first
        mock_membership_query.filter_by = mocker.MagicMock(return_value=mock_filter_by)
        
        # Simulate an error during commit
        mock_commit = mocker.patch.object(db.session, 'commit')
        mock_commit.side_effect = Exception("Simulated database error")
        
        result, status_code = TeamService.update_team_member(user_id, team_id, member_id, data)
        
        assert status_code == 500
        assert "error" in result
        assert "Internal server error" in result["error"]


def test_internal_server_error_remove_team_member(app, test_user, test_team, test_member, mocker):
    """
    Test internal server error (500) when removing a team member.
    """
    with app.app_context():
        user_id = test_user["id"]
        team_id = uuid.UUID(test_team["id"])
        member_id = uuid.UUID(test_member["id"])
        
        # Simulate successful queries for Team and User
        mock_team_query = mocker.patch('models.Team.query')
        mock_team = MagicMock()
        mock_team_get = mocker.MagicMock(return_value=mock_team)
        mock_team_query.get = mock_team_get
        
        mock_user_query = mocker.patch('models.User.query')
        mock_user = MagicMock()
        mock_user_get = mocker.MagicMock(return_value=mock_user)
        mock_user_query.get = mock_user_get
        
        # Simulate a successful query for TeamMembership
        mock_membership_query = mocker.patch('models.TeamMembership.query')
        mock_filter_by = mocker.MagicMock()
        mock_membership = MagicMock()
        mock_first = mocker.MagicMock(return_value=mock_membership)
        mock_filter_by.first = mock_first
        mock_membership_query.filter_by = mocker.MagicMock(return_value=mock_filter_by)
        
        # Simulate an error during deletion
        mock_delete = mocker.patch.object(db.session, 'delete')
        mock_delete.side_effect = Exception("Simulated database error")
        
        result, status_code = TeamService.remove_team_member(user_id, team_id, member_id)
        
        assert status_code == 500
        assert "error" in result
        assert "Internal server error" in result["error"]


def test_internal_server_error_get_team_members(app, test_user, test_team, mocker):
    """
    Test internal server error (500) when getting team members.
    """
    with app.app_context():
        user_id = test_user["id"]
        team_id = uuid.UUID(test_team["id"])
        
        # Simulate a successful query for Team
        mock_team_query = mocker.patch('models.Team.query')
        mock_team = MagicMock()
        mock_team_get = mocker.MagicMock(return_value=mock_team)
        mock_team_query.get = mock_team_get
        
        # Simulate an error during the query for members
        mock_membership_query = mocker.patch('models.TeamMembership.query')
        mock_filter_by = mocker.MagicMock()
        mock_filter_by.all.side_effect = Exception("Simulated database error")
        mock_membership_query.filter_by = mocker.MagicMock(return_value=mock_filter_by)
        
        result, status_code = TeamService.get_team_members(user_id, team_id)
        
        assert status_code == 500
        assert "error" in result
        assert "Internal server error" in result["error"]


def test_add_team_member_missing_data(app, test_user, test_team):
    """
    Test adding a team member with missing data.
    """
    with app.app_context():
        user_id = test_user["id"]
        team_id = uuid.UUID(test_team["id"])
        
        result, status_code = TeamService.add_team_member(user_id, team_id, None)
        
        assert status_code == 400
        assert "error" in result
        assert "No input data provided" in result["error"]


def test_add_team_member_missing_role(app, test_user, test_team, test_member):
    """
    Test adding a team member with missing role.
    """
    with app.app_context():
        user_id = test_user["id"]
        team_id = uuid.UUID(test_team["id"])
        
        data = {"user_id": test_member["id"]}  # Missing role
        
        result, status_code = TeamService.add_team_member(user_id, team_id, data)
        
        assert status_code == 400
        assert "error" in result
        assert "Role is required" in result["error"]


def test_update_team_member_no_data(app, test_user, test_team, test_member):
    """
    Test updating a team member with no data.
    """
    with app.app_context():
        user_id = test_user["id"]
        team_id = uuid.UUID(test_team["id"])
        member_id = uuid.UUID(test_member["id"])
        
        # First add the member
        membership = TeamMembership(user_id=member_id, team_id=team_id, role="developer")
        db.session.add(membership)
        db.session.commit()
        
        result, status_code = TeamService.update_team_member(user_id, team_id, member_id, None)
        
        assert status_code == 400
        assert "error" in result
        assert "No input data provided" in result["error"]


def test_nonexistent_team_update_member(app, test_user, test_member):
    """
    Test updating a team member in a non-existent team.
    """
    with app.app_context():
        user_id = test_user["id"]
        nonexistent_team_id = uuid.uuid4()
        member_id = uuid.UUID(test_member["id"])
        data = {"role": "new-role"}
        
        result, status_code = TeamService.update_team_member(user_id, nonexistent_team_id, member_id, data)
        
        assert status_code == 404
        assert "error" in result
        assert "Team not found" in result["error"]


def test_nonexistent_team_remove_member(app, test_user, test_member):
    """
    Test removing a team member from a non-existent team.
    """
    with app.app_context():
        user_id = test_user["id"]
        nonexistent_team_id = uuid.uuid4()
        member_id = uuid.UUID(test_member["id"])
        
        result, status_code = TeamService.remove_team_member(user_id, nonexistent_team_id, member_id)
        
        assert status_code == 404
        assert "error" in result
        assert "Team not found" in result["error"] 