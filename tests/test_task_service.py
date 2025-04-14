import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from werkzeug.security import generate_password_hash

from models import PriorityEnum, Project, StatusEnum, Task, User, db
from services.task_service import TaskService


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
            username=f"taskuser_{uuid.uuid4().hex[:8]}",
            email=f"taskuser_{uuid.uuid4().hex[:8]}@example.com",
            password_hash=generate_password_hash("password123"),
            role="member",
        )
        db.session.add(user)
        db.session.commit()
        return {"id": str(user.user_id), "username": user.username, "email": user.email}


@pytest.fixture(scope="function")
def test_project(app):
    """
    Fixture to create a test project.
    """
    with app.app_context():
        project = Project(
            title=f"Task Project {uuid.uuid4().hex[:8]}",
            description="Project for task testing",
            status="active",
        )
        db.session.add(project)
        db.session.commit()
        return {
            "id": str(project.project_id),
            "title": project.title,
            "description": project.description,
            "status": project.status,
        }


@pytest.fixture(scope="function")
def test_task(app, test_user, test_project):
    """
    Fixture to create a test task.
    """
    with app.app_context():
        user_id = test_user["id"]
        project_id = test_project["id"]
        
        task = Task(
            title=f"Test Task {uuid.uuid4().hex[:8]}",
            description="Task for testing services",
            priority=PriorityEnum.MEDIUM.value,
            status=StatusEnum.PENDING.value,
            deadline=datetime.utcnow() + timedelta(days=7),
            project_id=uuid.UUID(project_id),
            assignee_id=uuid.UUID(user_id),
            created_by=uuid.UUID(user_id),
            updated_by=uuid.UUID(user_id),
        )
        db.session.add(task)
        db.session.commit()
        
        return {
            "id": str(task.task_id),
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "project_id": project_id,
            "assignee_id": user_id,
        }


def test_create_task(app, test_user, test_project):
    """
    Test the TaskService.create_task method.
    """
    with app.app_context():
        user_id = test_user["id"]
        project_id = test_project["id"]
        
        data = {
            "title": f"New Task {uuid.uuid4().hex[:8]}",
            "description": "Created via service",
            "priority": PriorityEnum.HIGH.value,
            "status": StatusEnum.PENDING.value,
            "project_id": project_id,
            "assignee_id": user_id,
            "deadline": (datetime.utcnow() + timedelta(days=5)).isoformat(),
        }

        task_dict = TaskService.create_task(data, user_id)

        assert task_dict is not None
        assert task_dict["title"] == data["title"]
        assert task_dict["description"] == data["description"]
        assert task_dict["priority"] == PriorityEnum.HIGH.value
        assert task_dict["status"] == StatusEnum.PENDING.value
        assert task_dict["project_id"] == project_id
        assert task_dict["assignee_id"] == user_id
        assert "task_id" in task_dict


def test_create_task_with_string_priority(app, test_user, test_project):
    """
    Test the TaskService.create_task method with string priority.
    """
    with app.app_context():
        user_id = test_user["id"]
        project_id = test_project["id"]
        
        data = {
            "title": f"String Priority Task {uuid.uuid4().hex[:8]}",
            "description": "Task with string priority",
            "priority": "HIGH",
            "project_id": project_id,
            "assignee_id": user_id,
        }

        task_dict = TaskService.create_task(data, user_id)

        assert task_dict is not None
        assert task_dict["title"] == data["title"]
        assert task_dict["priority"] == PriorityEnum.HIGH.value


def test_create_task_invalid_project(app, test_user):
    """
    Test the TaskService.create_task method with invalid project ID.
    """
    with app.app_context():
        user_id = test_user["id"]
        nonexistent_project_id = str(uuid.uuid4())
        
        data = {
            "title": "Invalid Project Task",
            "description": "Task with invalid project",
            "project_id": nonexistent_project_id,
        }

        with pytest.raises(ValueError, match="Invalid project_id: Project not found"):
            TaskService.create_task(data, user_id)


def test_create_task_invalid_assignee(app, test_user, test_project):
    """
    Test the TaskService.create_task method with invalid assignee ID.
    """
    with app.app_context():
        user_id = test_user["id"]
        project_id = test_project["id"]
        nonexistent_assignee_id = str(uuid.uuid4())
        
        data = {
            "title": "Invalid Assignee Task",
            "description": "Task with invalid assignee",
            "project_id": project_id,
            "assignee_id": nonexistent_assignee_id,
        }

        with pytest.raises(ValueError, match="Invalid assignee_id: User not found"):
            TaskService.create_task(data, user_id)


def test_get_task(app, test_task):
    """
    Test the TaskService.get_task method.
    """
    with app.app_context():
        task_id = uuid.UUID(test_task["id"])
        
        task_dict = TaskService.get_task(task_id)
        
        assert task_dict is not None
        assert task_dict["task_id"] == test_task["id"]
        assert task_dict["title"] == test_task["title"]
        assert task_dict["description"] == test_task["description"]
        assert task_dict["status"] == test_task["status"]
        assert task_dict["priority"] == test_task["priority"]
        assert task_dict["project_id"] == test_task["project_id"]
        assert task_dict["assignee_id"] == test_task["assignee_id"]


def test_get_nonexistent_task(app):
    """
    Test the TaskService.get_task method with non-existent task ID.
    """
    with app.app_context():
        nonexistent_task_id = uuid.uuid4()
        
        with pytest.raises(ValueError, match="Task not found"):
            TaskService.get_task(nonexistent_task_id)


def test_update_task(app, test_task, test_user):
    """
    Test the TaskService.update_task method.
    """
    with app.app_context():
        task_id = uuid.UUID(test_task["id"])
        user_id = test_user["id"]
        
        data = {
            "title": f"Updated Task {uuid.uuid4().hex[:8]}",
            "description": "Updated via service",
            "status": StatusEnum.IN_PROGRESS.value,
            "priority": PriorityEnum.HIGH.value,
        }
        
        updated_task = TaskService.update_task(task_id, data, user_id)
        
        assert updated_task is not None
        assert updated_task["title"] == data["title"]
        assert updated_task["description"] == data["description"]
        assert updated_task["status"] == StatusEnum.IN_PROGRESS.value
        assert updated_task["priority"] == PriorityEnum.HIGH.value
        assert updated_task["task_id"] == test_task["id"]
        assert updated_task["updated_by"] == user_id


def test_update_task_with_string_priority(app, test_task, test_user):
    """
    Test the TaskService.update_task method with string priority.
    """
    with app.app_context():
        task_id = uuid.UUID(test_task["id"])
        user_id = test_user["id"]
        
        data = {
            "priority": "LOW",
        }
        
        updated_task = TaskService.update_task(task_id, data, user_id)
        
        assert updated_task is not None
        assert updated_task["priority"] == PriorityEnum.LOW.value
        assert updated_task["task_id"] == test_task["id"]


def test_update_task_invalid_status(app, test_task, test_user):
    """
    Test the TaskService.update_task method with invalid status.
    """
    with app.app_context():
        task_id = uuid.UUID(test_task["id"])
        user_id = test_user["id"]
        
        data = {
            "status": "invalid_status",
        }
        
        with pytest.raises(ValueError, match="Invalid status value"):
            TaskService.update_task(task_id, data, user_id)


def test_update_nonexistent_task(app, test_user):
    """
    Test the TaskService.update_task method with non-existent task.
    """
    with app.app_context():
        nonexistent_task_id = uuid.uuid4()
        user_id = test_user["id"]
        
        data = {
            "title": "Won't update",
        }
        
        with pytest.raises(ValueError, match="Task not found"):
            TaskService.update_task(nonexistent_task_id, data, user_id)


def test_delete_task(app, test_task):
    """
    Test the TaskService.delete_task method.
    """
    with app.app_context():
        task_id = uuid.UUID(test_task["id"])
        
        # Verify task exists before deletion
        task = Task.query.get(task_id)
        assert task is not None
        
        TaskService.delete_task(task_id)
        
        # Verify task was deleted
        deleted_task = Task.query.get(task_id)
        assert deleted_task is None


def test_delete_nonexistent_task(app):
    """
    Test the TaskService.delete_task method with non-existent task.
    """
    with app.app_context():
        nonexistent_task_id = uuid.uuid4()
        
        with pytest.raises(ValueError, match="Task not found"):
            TaskService.delete_task(nonexistent_task_id)


def test_get_tasks_with_filters(app, test_task, test_user, test_project):
    """
    Test the TaskService.get_tasks method with various filters.
    """
    with app.app_context():
        user_id = test_user["id"]
        project_id = test_project["id"]
        
        # Create a second task with different status
        second_task = Task(
            title=f"Second Task {uuid.uuid4().hex[:8]}",
            description="Another test task",
            priority=PriorityEnum.LOW.value,
            status=StatusEnum.IN_PROGRESS.value,
            project_id=uuid.UUID(project_id),
            assignee_id=uuid.UUID(user_id),
            created_by=uuid.UUID(user_id),
            updated_by=uuid.UUID(user_id),
        )
        db.session.add(second_task)
        db.session.commit()
        
        # Test filter by project_id
        project_filter = {"project_id": project_id}
        project_tasks = TaskService.get_tasks(project_filter)
        
        assert len(project_tasks) >= 2
        assert any(task["task_id"] == test_task["id"] for task in project_tasks)
        assert any(task["task_id"] == str(second_task.task_id) for task in project_tasks)
        
        # Test filter by assignee_id
        assignee_filter = {"assignee_id": user_id}
        assignee_tasks = TaskService.get_tasks(assignee_filter)
        
        assert len(assignee_tasks) >= 2
        assert any(task["assignee_id"] == user_id for task in assignee_tasks)
        
        # Test filter by status
        status_filter = {"status": StatusEnum.IN_PROGRESS.value}
        status_tasks = TaskService.get_tasks(status_filter)
        
        assert len(status_tasks) >= 1
        assert all(task["status"] == StatusEnum.IN_PROGRESS.value for task in status_tasks)
        assert any(task["task_id"] == str(second_task.task_id) for task in status_tasks)
        
        # Test combined filters
        combined_filter = {
            "project_id": project_id,
            "status": StatusEnum.IN_PROGRESS.value,
        }
        combined_tasks = TaskService.get_tasks(combined_filter)
        
        assert len(combined_tasks) >= 1
        assert all(task["project_id"] == project_id for task in combined_tasks)
        assert all(task["status"] == StatusEnum.IN_PROGRESS.value for task in combined_tasks)
        assert any(task["task_id"] == str(second_task.task_id) for task in combined_tasks)


def test_get_tasks_invalid_filters(app):
    """
    Test the TaskService.get_tasks method with invalid filters.
    """
    with app.app_context():
        # Test with non-existent project ID
        nonexistent_project_id = str(uuid.uuid4())
        project_filter = {"project_id": nonexistent_project_id}
        
        with pytest.raises(ValueError, match=f"Project with ID {nonexistent_project_id} not found"):
            TaskService.get_tasks(project_filter)
        
        # Test with non-existent assignee ID
        nonexistent_assignee_id = str(uuid.uuid4())
        assignee_filter = {"assignee_id": nonexistent_assignee_id}
        
        with pytest.raises(ValueError, match=f"User with ID {nonexistent_assignee_id} not found"):
            TaskService.get_tasks(assignee_filter)
        
        # Test with invalid status
        invalid_status_filter = {"status": "invalid_status"}
        
        with pytest.raises(ValueError, match="Invalid status value"):
            TaskService.get_tasks(invalid_status_filter) 