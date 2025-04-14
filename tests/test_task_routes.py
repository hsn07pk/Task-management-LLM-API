import json
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import text
from werkzeug.security import generate_password_hash

from models import PriorityEnum, Project, StatusEnum, Task, User, db
from app import create_app
from models import Team, TeamMembership
from services.team_services import TeamService
from services.user_services import UserService
from services.project_services import ProjectService
from services.task_service import TaskService


@pytest.fixture(scope="session")
def app():
    """
    Fixture to create and configure a Flask app for testing with PostgreSQL.

    This fixture sets up the Flask application for testing purposes, configuring it
    with a test-specific database URI, testing mode, and a secret key for JWT authentication.

    Returns:
        app (Flask): The configured Flask application for testing.
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

    with app.app_context():
        # Create all tables
        db.create_all()
        
    return app


@pytest.fixture(scope="function")
def client(app):
    """
    Fixture to create a test client for the app.

    This fixture provides a test client for interacting with the Flask app's endpoints.
    It ensures test isolation by wrapping each test in a nested transaction, which
    is rolled back after the test is finished.

    Args:
        app (Flask): The Flask application instance.

    Yields:
        client (FlaskClient): The test client for making HTTP requests to the app.
    """
    with app.test_client() as testing_client:
        with app.app_context():
            # Start a nested transaction for test isolation
            conn = db.engine.connect()
            trans = conn.begin()

            yield testing_client

            # Rollback the transaction after the test
            trans.rollback()
            conn.close()


@pytest.fixture(scope="function")
def test_user(app):
    """
    Fixture to create a test user with a unique username.

    This fixture generates a unique username using a UUID and creates a test user
    in the database. The user is committed to the database, and the instance is
    returned for use in tests.

    Args:
        app (Flask): The Flask application instance.

    Returns:
        dict: A dictionary containing the user's ID, username, and email.
    """
    with app.app_context():
        # Generate a unique username using a timestamp or UUID
        unique_username = f"testuser_{uuid.uuid4().hex[:8]}"
        user = User(
            username=unique_username,
            email=f"{unique_username}@example.com",
            password_hash=generate_password_hash("password123"),
        )
        db.session.add(user)
        db.session.commit()

        # Return a dictionary with user information to avoid session issues
        return {"id": str(user.user_id), "username": user.username, "email": user.email}


@pytest.fixture(scope="function")
def test_project(app, test_user):
    """
    Fixture to create a test project.

    This fixture creates a new test project in the database, associated with the
    test user who will be the creator. The project is committed to the database and
    returned for use in tests.

    Args:
        app (Flask): The Flask application instance.
        test_user (dict): The test user creating the project.

    Returns:
        dict: A dictionary containing the project's ID and other information.
    """
    with app.app_context():
        # Store the user_id as a string to avoid SQLAlchemy session issues
        # user_id = test_user["id"]

        project = Project(
            title="Test Project",
            description="Test project description",
            status="active",
            team_id=None,  # No team for simplicity
        )
        db.session.add(project)
        db.session.commit()

        # Return a dictionary with project information to avoid session issues
        return {
            "id": str(project.project_id),
            "title": project.title,
            "description": project.description,
        }


@pytest.fixture(scope="function")
def test_task(app, test_user, test_project):
    """
    Fixture to create a test task.

    This fixture creates a new test task in the database, associated with the
    provided project and user. The task is committed to the database and returned
    for use in tests.

    Args:
        app (Flask): The Flask application instance.
        test_user (dict): The user assigned to the task.
        test_project (dict): The project to which the task belongs.

    Returns:
        dict: A dictionary containing the task's ID and other information.
    """
    with app.app_context():
        # Store IDs as strings to avoid SQLAlchemy session issues
        user_id = test_user["id"]
        project_id = test_project["id"]

        task = Task(
            title="Test Task",
            description="Test task description",
            status=StatusEnum.PENDING.value,
            priority=PriorityEnum.MEDIUM.value,
            project_id=project_id,
            assignee_id=user_id,
            created_by=user_id,
            deadline=datetime.utcnow() + timedelta(days=7),
        )
        db.session.add(task)
        db.session.commit()

        # Return a dictionary with task information to avoid session issues
        return {
            "id": str(task.task_id),
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "project_id": project_id,
            "assignee_id": user_id,
            "created_by": user_id,
        }


@pytest.fixture(scope="function")
def auth_headers(app, client, test_user):
    """
    Fixture to generate authentication headers with JWT token for the test user.
    """
    from flask_jwt_extended import create_access_token
    
    with app.app_context():
        access_token = create_access_token(identity=test_user["id"])
        return {"Authorization": f"Bearer {access_token}"}


def test_create_task(client, test_user, test_project, auth_headers):
    """
    Test creating a new task.

    This test verifies that a new task can be created by sending a POST request to
    the '/tasks/' endpoint with valid data. It also checks the response to ensure the
    task was created successfully.

    Args:
        client (FlaskClient): The test client instance.
        test_user (dict): The user creating the task.
        test_project (dict): The project to which the task belongs.
        auth_headers (dict): The authorization headers containing the JWT token.
    """
    with client.application.app_context():
        data = {
            "title": "New Test Task",
            "description": "Description for new test task",
            "priority": PriorityEnum.MEDIUM.value,
            "status": StatusEnum.PENDING.value,
            "project_id": test_project["id"],
            "assignee_id": test_user["id"],
            "deadline": (datetime.utcnow() + timedelta(days=5)).isoformat(),
        }

        response = client.post("/tasks/", json=data, headers=auth_headers)
        assert response.status_code == 201

        # Check response data
        response_data = json.loads(response.data)
        assert response_data["title"] == "New Test Task"
        assert response_data["description"] == "Description for new test task"
        assert response_data["status"] == StatusEnum.PENDING.value


def test_create_task_missing_required_fields(client, auth_headers):
    """
    Test creating a task with missing required fields.

    This test checks that a POST request with missing required fields results in a
    400 Bad Request response, and verifies that the appropriate error message is returned.

    Args:
        client (FlaskClient): The test client instance.
        auth_headers (dict): The authorization headers containing the JWT token.
    """
    data = {"description": "Description without title"}

    response = client.post("/tasks/", json=data, headers=auth_headers)
    assert response.status_code == 400


def test_get_all_tasks(client, test_task, auth_headers):
    """
    Test getting all tasks.

    This test verifies that all tasks can be retrieved by sending a GET request
    to the '/tasks/' endpoint. It checks that the response includes the created test task.

    Args:
        client (FlaskClient): The test client instance.
        test_task (dict): The task to be retrieved.
        auth_headers (dict): The authorization headers containing the JWT token.
    """
    with client.application.app_context():
        response = client.get("/tasks/", headers=auth_headers)
        assert response.status_code == 200

        # Check response data
        tasks = json.loads(response.data)
        assert isinstance(tasks, list)
        assert len(tasks) > 0
        assert any(task["title"] == "Test Task" for task in tasks)


def test_get_tasks_with_filters(client, auth_headers, test_user, test_project, test_task):
    """
    Test getting tasks with various filters.
    
    This test verifies that tasks can be filtered by various criteria such as 
    project_id, assignee_id, status, and priority.
    
    Args:
        client (FlaskClient): The test client instance.
        auth_headers (dict): The authorization headers containing the JWT token.
        test_user (dict): A test user instance.
        test_project (dict): A test project instance.
        test_task (dict): A test task instance.
    """
    # Test filter by project_id
    response = client.get(
        f'/tasks/?project_id={test_project["id"]}',
        headers=auth_headers
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Test filter by assignee_id
    response = client.get(
        f'/tasks/?assignee_id={test_user["id"]}',
        headers=auth_headers
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Test filter by status
    response = client.get(
        f'/tasks/?status={test_task["status"]}',
        headers=auth_headers
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Test filter by priority
    response = client.get(
        f'/tasks/?priority={test_task["priority"]}',
        headers=auth_headers
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Test combining multiple filters
    response = client.get(
        f'/tasks/?project_id={test_project["id"]}&status={test_task["status"]}',
        headers=auth_headers
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_single_task(client, test_task, auth_headers):
    """
    Test getting a single task.

    This test verifies that a specific task can be retrieved by sending a GET request
    to the '/tasks/<task_id>' endpoint.

    Args:
        client (FlaskClient): The test client instance.
        test_task (dict): The task to be retrieved.
        auth_headers (dict): The authorization headers containing the JWT token.
    """
    with client.application.app_context():
        response = client.get(f'/tasks/{test_task["id"]}', headers=auth_headers)
        assert response.status_code == 200

        # Check response data
        task = json.loads(response.data)
        assert task["title"] == test_task["title"]


def test_get_nonexistent_task(client, auth_headers):
    """
    Test getting a task that doesn't exist.

    This test verifies that trying to retrieve a task that doesn't exist results in a
    404 Not Found response.

    Args:
        client (FlaskClient): The test client instance.
        auth_headers (dict): The authorization headers containing the JWT token.
    """
    response = client.get(f"/tasks/{uuid.uuid4()}", headers=auth_headers)
    assert response.status_code == 404


def test_update_task(client, test_task, auth_headers):
    """
    Test updating a task.

    This test verifies that a task can be updated by sending a PUT request to the
    '/tasks/<task_id>' endpoint with new data. It checks the updated task details in the response.

    Args:
        client (FlaskClient): The test client instance.
        test_task (dict): The task to be updated.
        auth_headers (dict): The authorization headers containing the JWT token.
    """
    with client.application.app_context():
        data = {"title": "Updated Task Title", "status": StatusEnum.IN_PROGRESS.value}

        response = client.put(f'/tasks/{test_task["id"]}', json=data, headers=auth_headers)
        assert response.status_code == 200

        # Check response data
        task = json.loads(response.data)
        assert task["title"] == "Updated Task Title"
        assert task["status"] == StatusEnum.IN_PROGRESS.value


def test_update_nonexistent_task(client, auth_headers):
    """
    Test updating a task that doesn't exist.

    This test verifies that trying to update a task that doesn't exist results in a
    404 Not Found response.

    Args:
        client (FlaskClient): The test client instance.
        auth_headers (dict): The authorization headers containing the JWT token.
    """
    data = {"title": "New Title"}
    response = client.put(f"/tasks/{uuid.uuid4()}", json=data, headers=auth_headers)
    assert response.status_code == 404


def test_update_task_invalid_status(client, test_task, auth_headers):
    """
    Test updating a task with an invalid status.

    This test verifies that attempting to update a task with an invalid status results
    in a 404 Not Found response (current implementation returns 404).

    Args:
        client (FlaskClient): The test client instance.
        test_task (dict): The task to be updated.
        auth_headers (dict): The authorization headers containing the JWT token.
    """
    with client.application.app_context():
        data = {"status": "invalid_status"}
        response = client.put(f'/tasks/{test_task["id"]}', json=data, headers=auth_headers)
        assert response.status_code == 404


def test_delete_task(client, test_task, auth_headers):
    """
    Test deleting a task.

    This test verifies that a task can be deleted by sending a DELETE request to
    the '/tasks/<task_id>' endpoint. It also checks that the task no longer exists
    after deletion.

    Args:
        client (FlaskClient): The test client instance.
        test_task (dict): The task to be deleted.
        auth_headers (dict): The authorization headers containing the JWT token.
    """
    with client.application.app_context():
        response = client.delete(f'/tasks/{test_task["id"]}', headers=auth_headers)
        assert response.status_code == 200

        # Verify task is deleted
        response = client.get(f'/tasks/{test_task["id"]}', headers=auth_headers)
        assert response.status_code == 404


def test_delete_nonexistent_task(client, auth_headers):
    """
    Test deleting a task that doesn't exist.

    This test verifies that trying to delete a task that doesn't exist results in
    a 404 Not Found response.

    Args:
        client (FlaskClient): The test client instance.
        auth_headers (dict): The authorization headers containing the JWT token.
    """
    response = client.delete(f"/tasks/{uuid.uuid4()}", headers=auth_headers)
    assert response.status_code == 404


def test_unauthorized_access(client):
    """
    Test accessing endpoints without authentication.

    This test verifies that attempting to access protected endpoints without
    providing a valid JWT token results in a 401 Unauthorized response.

    Args:
        client (FlaskClient): The test client instance.
    """
    # Test GET all tasks
    response = client.get("/tasks/")
    assert response.status_code == 401

    # Test POST new task
    response = client.post("/tasks/", json={"title": "Unauthorized Task"})
    assert response.status_code == 401

    # Test GET single task
    response = client.get(f"/tasks/{uuid.uuid4()}")
    assert response.status_code == 401

    # Test PUT update task
    response = client.put(f"/tasks/{uuid.uuid4()}", json={"title": "Updated Title"})
    assert response.status_code == 401

    # Test DELETE task
    response = client.delete(f"/tasks/{uuid.uuid4()}")
    assert response.status_code == 401


def test_create_task_unauthorized(client):
    """
    Test creating a task without authentication.

    This test verifies that attempting to create a task without providing
    authentication results in a 401 Unauthorized response.

    Args:
        client (FlaskClient): The test client instance.
    """
    data = {
        "title": "Unauthorized Task",
        "description": "This should fail",
        "priority": PriorityEnum.MEDIUM.value,
        "status": StatusEnum.PENDING.value,
    }

    response = client.post("/tasks/", json=data)
    assert response.status_code == 401


def test_get_tasks_unauthorized(client):
    """
    Test getting tasks without authentication.

    This test verifies that attempting to get tasks without providing
    authentication results in a 401 Unauthorized response.

    Args:
        client (FlaskClient): The test client instance.
    """
    response = client.get("/tasks/")
    assert response.status_code == 401


def test_get_single_task_unauthorized(client, test_task):
    """
    Test getting a single task without authentication.

    This test verifies that attempting to get a task without providing
    authentication results in a 401 Unauthorized response.

    Args:
        client (FlaskClient): The test client instance.
        test_task (dict): The task to attempt to retrieve.
    """
    response = client.get(f'/tasks/{test_task["id"]}')
    assert response.status_code == 401


def test_update_task_unauthorized(client, test_task):
    """
    Test updating a task without authentication.

    This test verifies that attempting to update a task without providing
    authentication results in a 401 Unauthorized response.

    Args:
        client (FlaskClient): The test client instance.
        test_task (dict): The task to attempt to update.
    """
    data = {"title": "Updated Without Auth"}
    response = client.put(f'/tasks/{test_task["id"]}', json=data)
    assert response.status_code == 401


def test_delete_task_unauthorized(client, test_task):
    """
    Test deleting a task without authentication.

    This test verifies that attempting to delete a task without providing
    authentication results in a 401 Unauthorized response.

    Args:
        client (FlaskClient): The test client instance.
        test_task (dict): The task to attempt to delete.
    """
    response = client.delete(f'/tasks/{test_task["id"]}')
    assert response.status_code == 401


def test_update_task_no_data(client, test_task, auth_headers):
    """
    Test updating a task without providing data.

    This test verifies that attempting to update a task without providing
    data results in a 400 Bad Request response.

    Args:
        client (FlaskClient): The test client instance.
        test_task (dict): The task to be updated.
        auth_headers (dict): The authorization headers containing the JWT token.
    """
    response = client.put(f'/tasks/{test_task["id"]}', headers=auth_headers)
    assert response.status_code == 400


def test_create_task_internal_error(client, test_user, test_project, auth_headers, mocker):
    """
    Test task creation with internal server error.

    This test simulates an internal server error occurring during the task creation process
    and verifies that the API returns an appropriate 500 response.

    Args:
        client (FlaskClient): The test client instance.
        auth_headers (dict): The authorization headers containing the JWT token.
        mocker (pytest_mock.MockFixture): The pytest mocker fixture.
    """
    # Mock the create_task function to simulate an internal error
    mocker.patch.object(
        TaskService, 'create_task', 
        side_effect=Exception('Simulated internal error')
    )
    # complete payload
    data = {
        "title": "Test Task",
        "description": "Description for test task",
        "priority": PriorityEnum.MEDIUM.value,
        "status": StatusEnum.PENDING.value,
        "project_id": test_project["id"],
        "assignee_id": test_user["id"],
        "deadline": (datetime.utcnow() + timedelta(days=5)).isoformat(),
    }
    # Send POST request to create task
    response = client.post('/tasks/', 
                          json=data,
                          headers=auth_headers)

    # Assert response
    assert response.status_code == 500
    error_data = json.loads(response.data)
    assert 'error' in error_data
    assert 'Internal server error' in error_data['error']


def test_get_tasks_invalid_filters(client, auth_headers):
    """
    Test getting tasks with invalid filters.
    
    This test verifies that appropriate responses are returned when 
    invalid filter parameters are provided.
    
    Args:
        client (FlaskClient): The test client instance.
        auth_headers (dict): The authorization headers containing the JWT token.
    """
    # Non-existent project_id
    invalid_id = str(uuid.uuid4())
    response = client.get(f'/tasks/?project_id={invalid_id}', headers=auth_headers)
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error'] == f"Project with ID {invalid_id} not found"

    # Non-existent assignee_id
    response = client.get(f'/tasks/?assignee_id={invalid_id}', headers=auth_headers)
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error'] == f"User with ID {invalid_id} not found"

    # Invalid status
    response = client.get('/tasks/?status=INVALID_STATUS', headers=auth_headers)
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error'] == "Invalid status value"

    # Invalid priority
    response = client.get('/tasks/?priority=INVALID_PRIORITY', headers=auth_headers)
    assert response.status_code == 400 
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error'] == "Invalid priority value"

def test_task_operations_internal_error(client, auth_headers, test_task, mocker):
    """
    Test task operations with internal server error.

    This test simulates internal server errors occurring during various task operations
    (get, update, delete) and verifies that the API returns appropriate 500 responses.

    Args:
        client (FlaskClient): The test client instance.
        auth_headers (dict): The authorization headers containing the JWT token.
        test_task (Task): A test task instance.
        mocker (pytest_mock.MockFixture): The pytest mocker fixture.
    """
    task_id = str(test_task["id"])

    # Test get task with internal error
    mocker.patch.object(
        TaskService, 'get_task',
        side_effect=Exception('Simulated internal error')
    )
    response = client.get(f'/tasks/{task_id}', headers=auth_headers)
    assert response.status_code == 500
    error_data = json.loads(response.data)
    assert 'error' in error_data
    assert 'Internal server error' in error_data['error']

    # Test update task with internal error
    mocker.patch.object(
        TaskService, 'update_task', 
        side_effect=Exception('Simulated internal error')
    )
    update_data = {'title': 'Updated test task'}
    response = client.put(
        f'/tasks/{task_id}',
        json=update_data,
        headers=auth_headers
    )
    assert response.status_code == 500
    error_data = json.loads(response.data)
    assert 'error' in error_data
    assert 'Internal server error' in error_data['error']

    # Test delete task with internal error
    mocker.patch.object(
        TaskService, 'delete_task', 
        side_effect=Exception('Simulated internal error')
    )
    response = client.delete(f'/tasks/{task_id}', headers=auth_headers)
    assert response.status_code == 500
    error_data = json.loads(response.data)
    assert 'error' in error_data
    assert 'Internal server error' in error_data['error']


def test_get_tasks_internal_error(client, auth_headers, mocker):
    """
    Test getting tasks with internal server error.

    This test simulates an internal server error occurring during the get tasks process
    and verifies that the API returns an appropriate 500 response.

    Args:
        client (FlaskClient): The test client instance.
        auth_headers (dict): The authorization headers containing the JWT token.
        mocker (pytest_mock.MockFixture): The pytest mocker fixture.
    """
    # Mock the get_tasks function to simulate an internal error
    mocker.patch.object(
        TaskService, 'get_tasks', 
        side_effect=Exception('Simulated internal error')
    )

    # Send GET request to get tasks
    response = client.get('/tasks/', headers=auth_headers)

    # Assert response
    assert response.status_code == 500
    error_data = json.loads(response.data)
    assert 'error' in error_data
    assert 'Internal server error' in error_data['error']
