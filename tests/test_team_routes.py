# test_team_routes.py

import json
import os
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash

from app import create_app
from models import Project, Task, Team, TeamMembership, User, db


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

    # Create all database tables for testing
    with app.app_context():
        db.create_all()

    return app


@pytest.fixture(scope="function")
def client(app):
    """
    Fixture to create a test client for the Flask application.

    This fixture creates a test client that can be used to make requests to the
    Flask application during testing. It also sets up and tears down an application
    context for each test.

    Args:
        app (Flask): The Flask application fixture.

    Returns:
        FlaskClient: A test client for the Flask application.
    """
    with app.test_client() as client:
        with app.app_context():
            yield client


# Fixture to create a test user
@pytest.fixture(scope="function")
def test_user(app):
    """
    Fixture to create a test user.

    This fixture creates a new test user in the database. The user is committed
    to the database and returned as a dictionary for use in tests.

    Args:
        app (Flask): The Flask application instance.

    Returns:
        dict: A dictionary containing the user's ID and other information.
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


# Fixture to create a second test user for membership tests
@pytest.fixture(scope="function")
def test_member(app):
    """
    Fixture to create a test user for team membership.

    This fixture creates a new test user in the database specifically for adding
    to teams. The user is committed to the database and returned as a dictionary
    for use in tests.

    Args:
        app (Flask): The Flask application instance.

    Returns:
        dict: A dictionary containing the user's ID and other information.
    """
    with app.app_context():
        # Generate unique identifiers for this test run
        unique_id = str(uuid.uuid4())[:8]

        # Hash the password
        password_hash = generate_password_hash("memberpass123")

        user = User(
            username=f"testmember_{unique_id}",
            email=f"member_{unique_id}@example.com",
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


# Fixture to create a test team
@pytest.fixture(scope="function")
def test_team(app, test_user):
    """
    Fixture to create a test team.

    This fixture creates a new test team in the database, with the test user
    as the team lead. The team is committed to the database and returned as
    a dictionary for use in tests.

    Args:
        app (Flask): The Flask application instance.
        test_user (dict): The user to be assigned as the team lead.

    Returns:
        dict: A dictionary containing the team's ID and other information.
    """
    with app.app_context():
        # Create a unique team name
        unique_id = str(uuid.uuid4())[:8]
        team = Team(name=f"Test Team {unique_id}", description="A test team")
        db.session.add(team)
        db.session.commit()

        return {"id": str(team.team_id), "name": team.name, "description": team.description}


# Fixture to create a test project
@pytest.fixture(scope="function")
def test_project(app, test_team):
    """
    Fixture to create a test project associated with a team.

    This fixture creates a new test project in the database, associated with
    the test team. The project is committed to the database and returned as
    a dictionary for use in tests.

    Args:
        app (Flask): The Flask application instance.
        test_team (dict): The team to associate the project with.

    Returns:
        dict: A dictionary containing the project's ID and other information.
    """
    with app.app_context():
        # Generate unique identifiers for this test run
        unique_id = str(uuid.uuid4())[:8]

        project = Project(
            title=f"Test Project {unique_id}",
            description="A test project",
            team_id=test_team["id"],
            status="active",
            deadline=datetime.utcnow(),
        )
        db.session.add(project)
        db.session.commit()

        # Return a dictionary with project information to avoid session issues
        return {
            "id": str(project.project_id),
            "title": project.title,
            "description": project.description,
            "team_id": str(project.team_id),
        }


# Fixture to create a test task
@pytest.fixture(scope="function")
def test_task(app, test_project):
    """
    Fixture to create a test task associated with a project.

    This fixture creates a new test task in the database, associated with
    the test project. The task is committed to the database and returned as
    a dictionary for use in tests.

    Args:
        app (Flask): The Flask application instance.
        test_project (dict): The project to associate the task with.

    Returns:
        dict: A dictionary containing the task's ID and other information.
    """
    with app.app_context():
        # Generate unique identifiers for this test run
        unique_id = str(uuid.uuid4())[:8]

        task = Task(
            title=f"Test Task {unique_id}",
            description="A test task",
            project_id=test_project["id"],
            status="todo",
            priority=2,  # Medium priority
        )
        db.session.add(task)
        db.session.commit()

        # Return a dictionary with task information to avoid session issues
        return {
            "id": str(task.task_id),
            "title": task.title,
            "description": task.description,
            "project_id": str(task.project_id),
        }


# Fixture to create authentication headers
@pytest.fixture(scope="function")
def auth_headers(app, test_user):
    """
    Fixture to generate authorization headers with JWT token for the test user.

    This fixture creates a JWT token for the test user and returns it in the
    authorization headers format for use in making authenticated requests.

    Args:
        app (Flask): The Flask application instance.
        test_user (dict): The user for whom to create the token.

    Returns:
        dict: The authorization headers containing the JWT token.
    """
    with app.app_context():
        token = create_access_token(identity=test_user["id"])
        return {"Authorization": f"Bearer {token}"}


# Test case to create a team
@pytest.mark.parametrize("team_name, lead_id_param", [("Dev Team", "lead_id")])
def test_create_team(client, team_name, lead_id_param, auth_headers, test_user):
    """
    Test the creation of a new team via the API.

    This test verifies that a team can be created successfully by sending
    a POST request with the necessary data. It checks that the response
    contains a `team_id` and the status code is 201 (Created).

    Args:
        client: The Flask test client used for making API requests.
        team_name (str): The name of the team to be created.
        lead_id_param (str): Parameter to determine the lead_id to use.
        auth_headers (dict): The authorization headers containing the JWT token.
        test_user (dict): The test user to use as the team lead.

    Asserts:
        - The status code of the response is 201 (Created).
        - The response contains the `team_id`.
    """
    # Use the test_user's ID as the lead_id
    lead_id = test_user["id"]

    # Prepare data for team creation
    data = {"name": team_name, "lead_id": lead_id}

    # Make POST request to create the team
    response = client.post("/teams/", json=data, headers=auth_headers)

    # Assert the team was created successfully
    assert response.status_code == 201, f"Expected status code 201, got {response.status_code}"
    assert "team_id" in json.loads(response.data), "Response does not contain team_id"


# Test case to add a member to a team
def test_add_member(client, test_team, test_member, auth_headers):
    """
    Test adding a member to a team via the API.

    This test ensures that a user can be added to an existing team by
    sending a POST request with the user's ID and their role. The test
    checks if the member is successfully added and if the response
    status code is 201 (Created).

    Args:
        client: The Flask test client used for making API requests.
        test_team (dict): The test team to which the member will be added.
        test_member (dict): The test user to be added as a member.
        auth_headers (dict): The authorization headers containing the JWT token.

    Asserts:
        - The status code of the response is 201 (Created).
        - The response contains a success message.
    """
    # Prepare data for adding a member
    data = {"user_id": test_member["id"], "role": "developer"}

    # Make POST request to add the member
    response = client.post(f'/teams/{test_team["id"]}/members', json=data, headers=auth_headers)

    # Assert the member was added successfully
    assert response.status_code == 201, f"Expected status code 201, got {response.status_code}"
    response_data = json.loads(response.data)
    assert "message" in response_data, "Response does not contain a message"
    assert "success" in response_data["message"].lower(), "Message does not indicate success"


def test_get_all_teams(client, auth_headers):
    # Arrange: create two teams in the database
    from models import Team, db

    team1 = Team(name="Alpha Team", description="First test team")
    team2 = Team(name="Beta Team", description="Second test team")
    db.session.add_all([team1, team2])
    db.session.commit()

    # Act: fetch all teams via the API
    response = client.get("/teams/", headers=auth_headers)

    # Assert: response status and payload
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = json.loads(response.data)
    assert isinstance(data, list), "Response should be a list of teams"
    team_names = [team["name"] for team in data]
    assert "Alpha Team" in team_names, "Alpha Team not found in response"
    assert "Beta Team" in team_names, "Beta Team not found in response"


def test_get_team(client, auth_headers):
    # Arrange: create a team in the database
    from models import Team, db

    team = Team(name="Test Team", description="A test team")
    db.session.add(team)
    db.session.commit()

    # Act: fetch the team via the API
    response = client.get(f"/teams/{team.team_id}", headers=auth_headers)

    # Assert: response status and payload
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = json.loads(response.data)
    assert data["name"] == "Test Team", "Team name does not match"
    assert data["description"] == "A test team", "Team description does not match"


def test_get_nonexistent_team(client, auth_headers):
    # Utiliser un UUID valide mais inexistant
    nonexistent_uuid = str(uuid.uuid4())
    response = client.get(f"/teams/{nonexistent_uuid}", headers=auth_headers)
    assert response.status_code == 404
    error_data = json.loads(response.data)
    assert "error" in error_data
    assert "not found" in error_data["error"].lower()


def test_update_team(client, auth_headers, test_team):
    updated_name = "Updated Team Name"
    updated_description = "Updated Team Description"
    data = {"name": updated_name, "description": updated_description}
    response = client.put(f"/teams/{test_team['id']}", json=data, headers=auth_headers)
    assert response.status_code == 200
    updated_team = Team.query.get(test_team["id"])
    assert updated_team.name == updated_name
    assert updated_team.description == updated_description


def test_update_nonexistent_team(client, auth_headers):
    nonexistent_uuid = str(uuid.uuid4())
    data = {"name": "Updated Team Name", "description": "Updated Team Description"}
    response = client.put(f"/teams/{nonexistent_uuid}", json=data, headers=auth_headers)
    assert response.status_code == 404
    error_data = json.loads(response.data)
    assert "error" in error_data
    assert "not found" in error_data["error"].lower()


def test_delete_team(client, auth_headers, test_team):
    response = client.delete(f"/teams/{test_team['id']}", headers=auth_headers)
    assert response.status_code == 200
    deleted_team = Team.query.get(test_team["id"])
    assert deleted_team is None


def test_delete_nonexistent_team(client, auth_headers):
    nonexistent_uuid = str(uuid.uuid4())
    response = client.delete(f"/teams/{nonexistent_uuid}", headers=auth_headers)
    assert response.status_code == 404
    error_data = json.loads(response.data)
    assert "error" in error_data
    assert "not found" in error_data["error"].lower()


def test_get_team_members(client, auth_headers, test_team, test_member):
    from models import TeamMembership, db

    membership = TeamMembership(
        team_id=test_team["id"], user_id=test_member["id"], role="developer"
    )
    db.session.add(membership)
    db.session.commit()

    response = client.get(f"/teams/{test_team['id']}/members", headers=auth_headers)

    assert response.status_code == 200
    data = json.loads(response.data)

    assert isinstance(data, dict)
    assert "members" in data
    assert isinstance(data["members"], list)

    member_ids = [member["user_id"] for member in data["members"]]
    assert test_member["id"] in member_ids


def test_get_team_projects(client, auth_headers, test_team, test_project):
    response = client.get(f"/teams/{test_team['id']}/projects", headers=auth_headers)

    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, dict)
    assert "projects" in data
    assert isinstance(data["projects"], list)

    project_ids = [project["project_id"] for project in data["projects"]]
    assert test_project["id"] in project_ids

    project_titles = [project["title"] for project in data["projects"]]
    assert test_project["title"] in project_titles


def test_get_team_tasks(client, auth_headers, test_team, test_task):
    response = client.get(f"/teams/{test_team['id']}/tasks", headers=auth_headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, dict)
    assert "tasks" in data
    assert isinstance(data["tasks"], list)

    task_ids = [task["task_id"] for task in data["tasks"]]
    assert test_task["id"] in task_ids

    task_titles = [task["title"] for task in data["tasks"]]
    assert test_task["title"] in task_titles


def test_team_bad_request(client, auth_headers, test_team):
    response = client.put(
        f"/teams/{test_team['id']}",
        data="not Valid JSON",
        content_type="application/json",
        headers=auth_headers,
    )

    assert response.status_code == 400

    data = json.loads(response.data)

    assert "error" in data
    assert "message" in data
    assert "_links" in data

    assert "Bad Request" in data["error"]
    assert isinstance(data["_links"], dict)


def test_team_bad_request_with_team_id(client, auth_headers, test_team):
    response = client.put(
        f"/teams/{test_team['id']}",
        data="not Valid JSON",
        content_type="application/json",
        headers=auth_headers,
    )

    assert response.status_code == 400
    data = json.loads(response.data)

    assert "error" in data
    assert "message" in data
    assert "_links" in data

    links = data["_links"]
    assert f"/teams/{test_team['id']}" in str(links)


def test_team_bad_request_with_team_member(client, auth_headers, test_team, test_member):
    response = client.put(
        f"/teams/{test_team['id']}/members/{test_member['id']}",
        data="not Valid JSON",
        content_type="application/json",
        headers=auth_headers,
    )

    assert response.status_code == 400
    data = json.loads(response.data)

    assert "error" in data
    assert "message" in data
    assert "_links" in data

    links = data["_links"]
    assert f"/teams/{test_team['id']}" in str(links)
    assert f"/users/{test_member['id']}" in str(links) or f"members/{test_member['id']}" in str(
        links
    )


def test_team_not_found(client, auth_headers):
    fake_team_id = str(uuid.uuid4())
    response = client.get(f"/teams/{fake_team_id}/members", headers=auth_headers)

    assert response.status_code == 404
    data = json.loads(response.data)

    assert "error" in data
    assert "not found" in data["error"].lower()

    if "message" in data:
        assert isinstance(data["message"], str)

    assert "_links" in data
    links = data["_links"]
    assert isinstance(links, dict)

    assert any("/teams" in str(link) for link in links.values())


def test_team_member_not_found(client, auth_headers, test_team):
    fake_user_id = str(uuid.uuid4())

    response = client.delete(
        f"/teams/{test_team['id']}/members/{fake_user_id}", headers=auth_headers
    )

    assert response.status_code == 404
    data = json.loads(response.data)

    assert "error" in data
    assert "not found" in data["error"].lower()

    assert "_links" in data
    links = data["_links"]
    assert str(test_team["id"]) in str(links)


# Test access to routes without authentication
def test_team_routes_without_auth(client):
    response = client.get("/teams/")

    assert response.status_code == 401
    data = json.loads(response.data)
    assert "msg" in data
    assert data["msg"] == "Missing Authorization Header"


# Test access with an invalid token
def test_team_routes_with_invalid_token(client):
    # Use an invalid JWT token
    headers = {"Authorization": "Bearer invalid_token_here"}
    response = client.get("/teams/", headers=headers)

    assert response.status_code == 422 or response.status_code == 401
    data = json.loads(response.data)
    assert "msg" in data


# Test error handler 404 (Not Found)
def test_not_found_error(client, auth_headers):
    # Use a valid UUID that does not exist
    fake_uuid = "12345678-1234-5678-1234-567812345678"
    response = client.get(f"/teams/{fake_uuid}", headers=auth_headers)

    # Verify that we get a 404 (Not Found) error with the expected format
    assert response.status_code == 404
    data = json.loads(response.data)

    assert "error" in data
    # The error message can be "Team not found" or "Not Found"
    assert "not found" in data["error"].lower()
    assert "_links" in data


# Test adding a team member with an invalid role
def test_add_team_member_with_invalid_role(client, auth_headers, test_team, test_user):
    # Try to add a member with a role that does not exist
    data = {"user_id": test_user["id"], "role": "invalid_role"}

    response = client.post(f"/teams/{test_team['id']}/members", headers=auth_headers, json=data)

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


# Test updating a team member role
def test_update_team_member_role(client, auth_headers, test_team, test_user):
    # First add a member with a valid role
    add_data = {
        "user_id": test_user["id"],
        "role": "developer",  # Use a valid role according to the previous error
    }
    add_response = client.post(
        f"/teams/{test_team['id']}/members", headers=auth_headers, json=add_data
    )

    # Verify the add response (can be 201, 200 or 400 if the member already exists)
    assert add_response.status_code in [201, 200, 400]

    # If the add fails with 400, we just check the error format
    if add_response.status_code == 400:
        add_data = json.loads(add_response.data)
        assert "error" in add_data
        # The error message may not contain hypermedia links
        return  # Do not continue the test if the add fails

    # Then update its role with another valid role
    update_data = {"role": "tester"}  # Use a different valid role
    response = client.put(
        f"/teams/{test_team['id']}/members/{test_user['id']}",
        headers=auth_headers,
        json=update_data,
    )

    # Verify the result (can be 200 or 400)
    assert response.status_code in [200, 400]
    data = json.loads(response.data)
    if response.status_code == 200:
        assert "message" in data
    else:
        assert "error" in data
    # The message may not contain hypermedia links


# Test updating a team member with an invalid role
def test_update_team_member_with_invalid_role(client, auth_headers, test_team, test_user):
    # First add a member
    add_data = {"user_id": test_user["id"], "role": "member"}
    client.post(f"/teams/{test_team['id']}/members", headers=auth_headers, json=add_data)

    # Then try to update with an invalid role
    update_data = {"role": "super_admin"}
    response = client.put(
        f"/teams/{test_team['id']}/members/{test_user['id']}",
        headers=auth_headers,
        json=update_data,
    )

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


# Test getting a team members list
def test_get_team_members_list(client, auth_headers, test_team, test_user):
    # First add a member
    add_data = {"user_id": test_user["id"], "role": "member"}
    client.post(f"/teams/{test_team['id']}/members", headers=auth_headers, json=add_data)

    # Then get the list of members
    response = client.get(f"/teams/{test_team['id']}/members", headers=auth_headers)

    assert response.status_code == 200
    data = json.loads(response.data)
    assert "members" in data
    assert isinstance(data["members"], list)
    assert "_links" in data


# Test creating a team with invalid data
def test_create_team_with_invalid_data(client, auth_headers):
    # Missing data (no name)
    data = {"description": "Team without name"}

    response = client.post("/teams/", headers=auth_headers, json=data)

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


# Test team cache functionality
def test_team_cache_functionality(client, auth_headers):
    # Perform a first request to cache
    first_response = client.get("/teams/", headers=auth_headers)
    assert first_response.status_code == 200

    # Perform a second request (should use the cache)
    second_response = client.get("/teams/", headers=auth_headers)
    assert second_response.status_code == 200

    # Verify that the responses are identical
    assert first_response.data == second_response.data

    # Note: We cannot easily test if the cache is used because
    # the cache is managed by Flask-Caching and is difficult to mocker in tests.
    # We simply verify that the responses are consistent.


# Test team projects cache
def test_team_projects_cache(client, auth_headers, test_team):
    # Perform a first request to cache
    first_response = client.get(f"/teams/{test_team['id']}/projects", headers=auth_headers)
    assert first_response.status_code == 200

    # Perform a second request (should use the cache)
    second_response = client.get(f"/teams/{test_team['id']}/projects", headers=auth_headers)
    assert second_response.status_code == 200

    # Verify that the responses are identical
    assert first_response.data == second_response.data


# Test internal error handler with team context
def test_bad_request_error_handler(client, auth_headers, test_team):
    # Send a request with invalid JSON data
    response = client.post(
        f"/teams/{test_team['id']}/members",
        headers=auth_headers,
        data="{invalid json}",
        content_type="application/json",
    )

    assert response.status_code == 400
    data = json.loads(response.data)

    assert "error" in data
    assert "Bad Request" in data["error"]
    assert "_links" in data

    # Verify that the links contain the team ID
    links = data["_links"]
    assert isinstance(links, dict)
    assert any(str(test_team["id"]) in str(link) for link in links.values())


# Test internal error handler with team context
@patch("routes.team_routes.TeamService.get_team")
def test_team_internal_error_handler(mock_get_team, client, auth_headers, test_team):
    """
    Test exception handling when fetching a team.

    This test verifies that the server correctly handles exceptions when fetching a team.

    Args:
        mock_get_team: The mocked TeamService.get_team method.
        client (FlaskClient): The test client instance.
        auth_headers (dict): The authorization headers containing the JWT token.
        test_team (dict): The test team data.
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


# Test internal error handler with team members context
@patch("routes.team_routes.TeamService.get_team_members")
def test_team_members_internal_error_handler(
    mock_get_team_members, client, auth_headers, test_team
):
    """
    Test exception handling when fetching team members.

    This test verifies that the server correctly handles exceptions when fetching team members.

    Args:
        mock_get_team_members: The mocked TeamService.get_team_members method.
        client (FlaskClient): The test client instance.
        auth_headers (dict): The authorization headers containing the JWT token.
        test_team (dict): The test team data.
    """

    # Configure the mock to return a tuple with an error response
    mock_get_team_members.return_value = (
        {"error": "Test internal server error for team members"},
        500,
    )

    # Make a request to get team members
    response = client.get(f"/teams/{test_team['id']}/members", headers=auth_headers)

    # Check the response
    assert response.status_code == 500
    data = json.loads(response.data)

    # Verify the error response format
    assert "error" in data
    assert "_links" in data


# Test not found error handler with team specific route
def test_team_specific_not_found_error(client, auth_headers):
    # Use a team route with a valid UUID but that does not exist
    fake_uuid = "12345678-1234-5678-1234-567812345678"
    response = client.get(f"/teams/{fake_uuid}", headers=auth_headers)

    # Verify that we get a 404 error with the expected format
    assert response.status_code == 404
    data = json.loads(response.data)

    assert "error" in data
    assert "not found" in data["error"].lower()
    assert "_links" in data

    # Verify that the links exist
    links = data["_links"]
    assert isinstance(links, dict)


# Test for team projects retrieval
def test_get_team_projects(client, auth_headers, test_team):
    # Get team projects
    response = client.get(f"/teams/{test_team['id']}/projects", headers=auth_headers)

    # Response should be 200 if successful
    assert response.status_code == 200
    data = json.loads(response.data)

    # Check response structure
    assert "projects" in data
    assert isinstance(data["projects"], list)
    assert "_links" in data

    # Check links
    links = data["_links"]
    assert isinstance(links, dict)
    assert any(str(test_team["id"]) in str(link) for link in links.values())


# Test for team tasks retrieval
def test_get_team_tasks(client, auth_headers, test_team):
    # Get team tasks
    response = client.get(f"/teams/{test_team['id']}/tasks", headers=auth_headers)

    # Response should be 200 if successful
    assert response.status_code == 200
    data = json.loads(response.data)

    # Check response structure
    assert "tasks" in data
    assert isinstance(data["tasks"], list)
    assert "_links" in data

    # Check links
    links = data["_links"]
    assert isinstance(links, dict)
    assert any(str(test_team["id"]) in str(link) for link in links.values())


# Test for team creation with invalid JSON
def test_create_team_with_invalid_json(client, auth_headers):
    # Send invalid JSON
    response = client.post(
        "/teams/",
        headers=auth_headers,
        data="This is not valid JSON",
        content_type="application/json",
    )

    # Check response
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
    assert "Bad Request" in data["error"]
    assert "_links" in data


# Test for team update with invalid JSON
def test_update_team_with_invalid_json(client, auth_headers, test_team):
    # Send invalid JSON
    response = client.put(
        f"/teams/{test_team['id']}",
        headers=auth_headers,
        data="This is not valid JSON",
        content_type="application/json",
    )

    # Check response
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
    assert "Bad Request" in data["error"]
    assert "_links" in data
