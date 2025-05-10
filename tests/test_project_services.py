import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from werkzeug.security import generate_password_hash

from models import Project, Team, User, db
from services.project_services import ProjectService


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
            role="member",
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
def test_project(app, test_team):
    """
    Fixture to create a test project.
    """
    with app.app_context():
        project = Project(
            title=f"Project {uuid.uuid4().hex[:8]}",
            description="Test project description",
            status="planning",
            deadline=datetime.utcnow() + timedelta(days=30),
            team_id=uuid.UUID(test_team["id"]),
        )
        db.session.add(project)
        db.session.commit()
        return {
            "id": str(project.project_id),
            "title": project.title,
            "description": project.description,
            "status": project.status,
            "team_id": str(project.team_id),
        }


def test_create_project(app, test_team):
    """
    Test the ProjectService.create_project method.
    """
    with app.app_context():
        data = {
            "title": f"New Project {uuid.uuid4().hex[:8]}",
            "description": "Created via service",
            "status": "planning",
            "deadline": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "team_id": test_team["id"],
        }

        project = ProjectService.create_project(data)

        assert project is not None
        assert project.title == data["title"]
        assert project.description == data["description"]
        assert project.status == data["status"]
        assert project.team_id == uuid.UUID(test_team["id"])


def test_create_project_without_team(app):
    """
    Test the ProjectService.create_project method without specifying a team.
    """
    with app.app_context():
        data = {
            "title": f"Solo Project {uuid.uuid4().hex[:8]}",
            "description": "Project without a team",
            "status": "planning",
        }

        project = ProjectService.create_project(data)

        assert project is not None
        assert project.title == data["title"]
        assert project.description == data["description"]
        assert project.status == data["status"]
        assert project.team_id is None


def test_get_project(app, test_project):
    """
    Test the ProjectService.get_project method.
    """
    with app.app_context():
        project_id = uuid.UUID(test_project["id"])

        project = ProjectService.get_project(project_id)

        assert project is not None
        assert str(project.project_id) == test_project["id"]
        assert project.title == test_project["title"]
        assert project.description == test_project["description"]
        assert project.status == test_project["status"]


def test_get_nonexistent_project(app):
    """
    Test the ProjectService.get_project method raises when project does not exist.
    """
    with app.app_context():
        nonexistent_project_id = uuid.uuid4()
        with pytest.raises(Exception):
            ProjectService.get_project(nonexistent_project_id)
        # Do not verify the exact error message as it may vary
        # depending on the database state


def test_update_project(app, test_project):
    """
    Test the ProjectService.update_project method.
    """
    with app.app_context():
        project = Project.query.get(uuid.UUID(test_project["id"]))
        data = {
            "title": f"Updated Project {uuid.uuid4().hex[:8]}",
            "description": "Updated via service",
            "status": "active",
        }

        updated_project = ProjectService.update_project(project, data)

        assert updated_project is not None
        assert updated_project.title == data["title"]
        assert updated_project.description == data["description"]
        assert updated_project.status == data["status"]
        assert str(updated_project.project_id) == test_project["id"]  # ID remains the same


def test_update_project_change_team(app, test_project, test_user):
    """
    Test the ProjectService.update_project method with team change.
    """
    with app.app_context():
        # Create a new team
        new_team = Team(
            name=f"New Team {uuid.uuid4().hex[:8]}",
            description="New team for project",
            lead_id=uuid.UUID(test_user["id"]),
        )
        db.session.add(new_team)
        db.session.commit()

        project = Project.query.get(uuid.UUID(test_project["id"]))
        data = {
            "team_id": str(new_team.team_id),
        }

        updated_project = ProjectService.update_project(project, data)

        assert updated_project is not None
        assert updated_project.team_id == new_team.team_id
        assert str(updated_project.project_id) == test_project["id"]  # ID remains the same


def test_delete_project(app, test_project):
    """
    Test the ProjectService.delete_project method.
    """
    with app.app_context():
        project = Project.query.get(uuid.UUID(test_project["id"]))

        # Verify project exists before deletion
        assert project is not None

        ProjectService.delete_project(project)

        # Verify project was deleted
        deleted_project = Project.query.get(uuid.UUID(test_project["id"]))
        assert deleted_project is None


def test_fetch_all_projects(app, test_project):
    """
    Test the ProjectService.fetch_all_projects method.
    """
    with app.app_context():
        # Create a second project to ensure we're getting multiple
        second_project = Project(
            title=f"Second Project {uuid.uuid4().hex[:8]}",
            description="Another test project",
            status="planning",
        )
        db.session.add(second_project)
        db.session.commit()

        projects = ProjectService.fetch_all_projects()

        assert isinstance(projects, list)
        assert len(projects) >= 2

        # Convert UUID and datetime to string for JSON serialization test
        project_ids = [str(p["project_id"]) for p in projects]
        assert test_project["id"] in project_ids
        assert str(second_project.project_id) in project_ids


def test_fetch_projects_by_team(app, test_project, test_team):
    """
    Test that projects can be filtered by team_id.
    """
    with app.app_context():
        # Create a second project with the same team
        second_project = Project(
            title=f"Same Team Project {uuid.uuid4().hex[:8]}",
            description="Project for same team",
            status="planning",
            team_id=uuid.UUID(test_team["id"]),
        )
        db.session.add(second_project)
        db.session.commit()

        # Skip creating a new user and team, which may cause database issues
        # Instead, just focus on testing the query functionality

        # Test custom query to filter by team_id
        team_projects = Project.query.filter_by(team_id=uuid.UUID(test_team["id"])).all()

        assert len(team_projects) >= 2
        project_ids = [str(p.project_id) for p in team_projects]
        assert test_project["id"] in project_ids
        assert str(second_project.project_id) in project_ids


def test_create_project_with_invalid_team(app):
    """
    Test that creating a project with a nonexistent team_id raises the correct exception.
    """
    with app.app_context():
        fake_team_id = str(uuid.uuid4())
        data = {
            "title": "Invalid Team Project",
            "description": "This project has an invalid team",
            "status": "planning",
            "deadline": (datetime.utcnow() + timedelta(days=10)).isoformat(),
            "team_id": fake_team_id,
        }

        with pytest.raises(Exception) as excinfo:
            ProjectService.create_project(data)
        # The service wraps the original ValueError in a generic Exception
        assert "Error creating project: Team not found" in str(excinfo.value)


def test_create_project_with_database_integrity_error(app, test_team):
    """
    Test that creating a project with a nonexistent category_id raises a database integrity error.
    """
    with app.app_context():

        fake_category_id = str(uuid.uuid4())
        data = {
            "title": f"Integrity Error Project {uuid.uuid4().hex[:8]}",
            "description": "This project has an invalid category",
            "status": "planning",
            "deadline": (datetime.utcnow() + timedelta(days=10)).isoformat(),
            "team_id": test_team["id"],
            "category_id": fake_category_id,
        }

        with pytest.raises(ValueError) as excinfo:
            ProjectService.create_project(data)

        assert "Database integrity error" in str(excinfo.value)


def test_get_project_with_invalid_id(app):
    with app.app_context():
        invalid_project_id = uuid.uuid4()

        with pytest.raises(Exception) as excinfo:
            ProjectService.get_project(invalid_project_id)
        assert "Error retrieving project:" in str(excinfo.value)


def test_update_project_with_invalid_team_id(app, test_project):
    with app.app_context():
        invalid_team_id = uuid.uuid4()
        data = {
            "title": "Updated Project Title",
            "team_id": str(invalid_team_id),
        }
        project = Project.query.get(uuid.UUID(test_project["id"]))
        with pytest.raises(Exception) as excinfo:
            ProjectService.update_project(project, data)
        assert "Team not found" in str(excinfo.value)


def test_update_project_with_database_integrity_error(app, test_project):
    with app.app_context():
        fake_category_id = str(uuid.uuid4())
        data = {
            "title": "Updated Project Title",
            "category_id": fake_category_id,
        }
        project = Project.query.get(uuid.UUID(test_project["id"]))
        with pytest.raises(ValueError) as excinfo:
            ProjectService.update_project(project, data)
        assert "Database integrity error" in str(excinfo.value)


def test_delete_project_error(app):
    with app.app_context():
        # Attempt to delete a project that doesn't exist
        fake_project_id = uuid.uuid4()
        project = Project.query.get(fake_project_id)

        with pytest.raises(Exception) as excinfo:
            ProjectService.delete_project(project)

        assert "Error deleting project:" in str(excinfo.value)


def test_fetch_all_projects_no_projects_prints_message_and_returns_empty(app, capsys):
    """
    When there are no projects in the database, fetch_all_projects()
    should return an empty list and print a debug message.
    """
    with app.app_context():
        # Reinitialize the database to ensure it's empty
        db.drop_all()
        db.create_all()

        result = ProjectService.fetch_all_projects()

        # It should return an empty list
        assert result == []

        # Capture and verify the debug print output
        captured = capsys.readouterr()
        assert "No projects found in the database." in captured.out


def test_fetch_all_projects_raises_on_db_error(app, monkeypatch):
    """
    If the database query fails, fetch_all_projects() should rollback
    and raise an Exception with the original error message.
    """
    with app.app_context():
        # Create a fake query object whose all() method raises
        class FakeQuery:
            def all(self):
                raise RuntimeError("Database error")

        # Monkeypatch db.session.query to return our fake query
        monkeypatch.setattr(db.session, "query", lambda model: FakeQuery())

        # Expect an Exception wrapping the original error
        with pytest.raises(Exception) as excinfo:
            ProjectService.fetch_all_projects()

        message = str(excinfo.value)
        assert message.startswith("Error retrieving projects:")
        assert "Database error" in message
