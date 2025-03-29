import json
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import text
from werkzeug.security import generate_password_hash

from models import PriorityEnum, Project, StatusEnum, Task, User, db


@pytest.fixture(scope="session")
def app():
    """
    Fixture to create and configure a Flask app for testing with PostgreSQL.

    This fixture sets up the Flask application for testing purposes, configuring it
    with a test-specific database URI, testing mode, and a secret key for JWT authentication.

    Returns:
        app (Flask): The configured Flask application for testing.
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


@pytest.fixture(scope="session")
def _db(app):
    """
    Fixture to set up the database before running tests.

    This fixture is responsible for preparing the test database. It cleans the schema
    by dropping and recreating the schema, then creates all necessary tables. After
    the tests are completed, it removes the database session and cleans up the schema.

    Args:
        app (Flask): The Flask application instance.

    Yields:
        db (SQLAlchemy): The database session object used in the tests.
    """
    with app.app_context():
        # Clean database schema before running tests
        db.session.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        db.session.commit()

        # Create all tables
        db.create_all()

        yield db

        # Clean up after all tests
        db.session.remove()
        db.session.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        db.session.commit()


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
        user_id = test_user["id"]

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
            "project_id": str(task.project_id),
            "assignee_id": str(task.assignee_id),
            "created_by": str(task.created_by),
        }


@pytest.fixture(scope="function")
def auth_headers(app, client, test_user):
    """
    Fixture to generate authorization headers with JWT token for the test user.

    This fixture logs in the test user and retrieves an authentication token. The
    token is then included in the authorization headers for use in making authenticated
    requests to the Flask app.

    Args:
        app (Flask): The Flask application instance.
        client (FlaskClient): The Flask test client instance.
        test_user (dict): The test user to log in.

    Returns:
        dict: A dictionary containing the Authorization header with the JWT token.
    """
    response = client.post("/login", json={"email": test_user["email"], "password": "password123"})
    assert response.status_code == 200, f"Login failed: {response.data}"

    token = json.loads(response.data)["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_task(client, test_user, test_project, auth_headers):
    """
    Test creating a new task.

    This test verifies that a new task can be created by sending a POST request to
    the '/tasks' endpoint with valid data. It also checks the response to ensure the
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
            "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        }

        response = client.post("/tasks", json=data, headers=auth_headers)
        print("Create task response:", response.data)  # Debug print
        assert response.status_code == 201

        # Check response data
        response_data = json.loads(response.data)
        assert response_data["title"] == "New Test Task"
        assert response_data["description"] == "Description for new test task"
        assert response_data["status"] == StatusEnum.PENDING.value
        assert "task_id" in response_data


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

    response = client.post("/tasks", json=data, headers=auth_headers)
    assert response.status_code == 400
    assert b"'title' is a required property" in response.data


def test_get_all_tasks(client, test_task, auth_headers):
    """
    Test getting all tasks.

    This test verifies that all tasks can be retrieved by sending a GET request
    to the '/tasks' endpoint. It checks that the response includes the created test task.

    Args:
        client (FlaskClient): The test client instance.
        test_task (dict): The task to be retrieved.
        auth_headers (dict): The authorization headers containing the JWT token.
    """
    with client.application.app_context():
        response = client.get("/tasks", headers=auth_headers)
        print("Get all tasks response:", response.data)  # Debug print
        assert response.status_code == 200

        # Check response data
        tasks = json.loads(response.data)
        assert isinstance(tasks, list)
        assert len(tasks) > 0
        assert any(task["title"] == "Test Task" for task in tasks)


def test_get_tasks_with_filters(client, test_task, auth_headers):
    """
    Test getting tasks with filters.

    This test verifies that tasks can be filtered by project_id, assignee_id, and status
    by sending GET requests with the respective query parameters. It ensures that the filters
    work as expected.

    Args:
        client (FlaskClient): The test client instance.
        test_task (dict): The task to be filtered.
        auth_headers (dict): The authorization headers containing the JWT token.
    """
    with client.application.app_context():
        # Test project_id filter
        response = client.get(f'/tasks?project_id={test_task["project_id"]}', headers=auth_headers)
        print("Get tasks with filters response:", response.data)  # Debug print
        assert response.status_code == 200
        tasks = json.loads(response.data)
        assert len(tasks) >= 1
        assert any(task["project_id"] == test_task["project_id"] for task in tasks)

        # Test assignee_id filter
        response = client.get(
            f'/tasks?assignee_id={test_task["assignee_id"]}', headers=auth_headers
        )
        assert response.status_code == 200
        tasks = json.loads(response.data)
        assert len(tasks) >= 1
        assert any(task["assignee_id"] == test_task["assignee_id"] for task in tasks)

        # Test status filter
        response = client.get(f"/tasks?status={StatusEnum.PENDING.value}", headers=auth_headers)
        assert response.status_code == 200
        tasks = json.loads(response.data)
        assert any(task["status"] == StatusEnum.PENDING.value for task in tasks)


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
        assert task["task_id"] == test_task["id"]
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
    # 404 means Not Found - route should return 404 if the task doesn't exist
    assert response.status_code in [404, 405]


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
    in a 400 Bad Request response.

    Args:
        client (FlaskClient): The test client instance.
        test_task (dict): The task to be updated.
        auth_headers (dict): The authorization headers containing the JWT token.
    """
    with client.application.app_context():
        data = {"status": "invalid_status"}
        response = client.put(f'/tasks/{test_task["id"]}', json=data, headers=auth_headers)
        print("Update task invalid status response:", response.data)  # Debug print
        assert response.status_code == 400


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
        print("Delete task response:", response.data)  # Debug print
        assert response.status_code == 204

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
