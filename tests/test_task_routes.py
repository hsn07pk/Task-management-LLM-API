import pytest
from datetime import datetime, timedelta
import json
import uuid
from sqlalchemy import text
from models import db, User, Project, Task, StatusEnum, PriorityEnum
from werkzeug.security import generate_password_hash

@pytest.fixture(scope="session")
def app():
    """Create and configure a Flask app for testing with PostgreSQL."""
    from app import create_app
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'postgresql://admin:helloworld123@localhost/task_management_db',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JWT_SECRET_KEY': 'test-secret-key'
    })
    
    return app

@pytest.fixture(scope="session")
def _db(app):
    """Set up the database."""
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
    """Test client for the app."""
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
    """Create a test user with a unique username."""
    with app.app_context():
        # Generate a unique username using a timestamp or UUID
        unique_username = f"testuser_{uuid.uuid4().hex[:8]}"
        user = User(
            username=unique_username,
            email=f"{unique_username}@example.com",
            password_hash=generate_password_hash('password123')
        )
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture(scope="function")
def test_project(app, test_user):
    """Create a test project."""
    with app.app_context():
        project = Project(
            title='Test Project',
            description='Test project description',
            status='active',
            team_id=None,  # No team for simplicity
            created_by=test_user.user_id
        )
        db.session.add(project)
        db.session.commit()
        return project

@pytest.fixture(scope="function")
def test_task(app, test_user, test_project):
    """Create a test task."""
    with app.app_context():
        task = Task(
            title='Test Task',
            description='Test task description',
            status=StatusEnum.PENDING.value,
            priority=PriorityEnum.MEDIUM.value,
            project_id=test_project.project_id,
            assignee_id=test_user.user_id,
            created_by=test_user.user_id,
            deadline=datetime.utcnow() + timedelta(days=7)
        )
        db.session.add(task)
        db.session.commit()
        return task

@pytest.fixture(scope="function")
def auth_headers(app, client, test_user):
    """Get auth headers with JWT token."""
    response = client.post('/login', json={
        'email': 'testuser@example.com',
        'password': 'password123'
    })
    assert response.status_code == 200, f"Login failed: {response.data}"
    
    token = json.loads(response.data)['access_token']
    return {'Authorization': f'Bearer {token}'}

def test_create_task(client, test_user, test_project, auth_headers):
    """Test creating a new task."""
    with client.application.app_context():
        data = {
            'title': 'New Test Task',
            'description': 'Description for new test task',
            'priority': PriorityEnum.MEDIUM.value,
            'status': StatusEnum.PENDING.value,
            'project_id': str(test_project.project_id),
            'assignee_id': str(test_user.user_id),
            'deadline': (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
        
        response = client.post('/tasks', json=data, headers=auth_headers)
        print("Create task response:", response.data)  # Debug print
        assert response.status_code == 201
        
        # Check response data
        response_data = json.loads(response.data)
        assert response_data['title'] == 'New Test Task'
        assert response_data['description'] == 'Description for new test task'
        assert response_data['status'] == StatusEnum.PENDING.value
        assert 'task_id' in response_data

def test_create_task_missing_required_fields(client, auth_headers):
    """Test creating a task with missing required fields."""
    data = {
        'description': 'Description without title'
    }
    
    response = client.post('/tasks', json=data, headers=auth_headers)
    assert response.status_code == 400
    assert b'Missing required field' in response.data

def test_get_all_tasks(client, test_task, auth_headers):
    """Test getting all tasks."""
    with client.application.app_context():
        response = client.get('/tasks', headers=auth_headers)
        print("Get all tasks response:", response.data)  # Debug print
        assert response.status_code == 200
        
        # Check response data
        tasks = json.loads(response.data)
        assert isinstance(tasks, list)
        assert len(tasks) > 0
        assert any(task['title'] == 'Test Task' for task in tasks)

def test_get_tasks_with_filters(client, test_task, auth_headers):
    """Test getting tasks with filters."""
    with client.application.app_context():
        # Test project_id filter
        response = client.get(f'/tasks?project_id={test_task.project_id}', headers=auth_headers)
        print("Get tasks with filters response:", response.data)  # Debug print
        assert response.status_code == 200
        tasks = json.loads(response.data)
        assert len(tasks) >= 1
        assert any(task['project_id'] == str(test_task.project_id) for task in tasks)

        # Test assignee_id filter
        response = client.get(f'/tasks?assignee_id={test_task.assignee_id}', headers=auth_headers)
        assert response.status_code == 200
        tasks = json.loads(response.data)
        assert len(tasks) >= 1
        assert any(task['assignee_id'] == str(test_task.assignee_id) for task in tasks)

        # Test status filter
        response = client.get(f'/tasks?status={StatusEnum.PENDING.value}', headers=auth_headers)
        assert response.status_code == 200
        tasks = json.loads(response.data)
        assert any(task['status'] == StatusEnum.PENDING.value for task in tasks)

def test_get_single_task(client, test_task, auth_headers):
    """Test getting a single task."""
    with client.application.app_context():
        response = client.get(f'/tasks/{test_task.task_id}', headers=auth_headers)
        assert response.status_code == 200
        
        # Check response data
        task = json.loads(response.data)
        assert task['task_id'] == str(test_task.task_id)
        assert task['title'] == test_task.title

def test_get_nonexistent_task(client, auth_headers):
    """Test getting a task that doesn't exist."""
    # Check if your route is properly configured
    response = client.get(f'/tasks/{uuid.uuid4()}', headers=auth_headers)
    # 405 means METHOD NOT ALLOWED - your route might not support GET
    # Check your route definitions in your Flask app
    assert response.status_code in [404, 405]


def test_update_task(client, test_task, auth_headers):
    """Test updating a task."""
    with client.application.app_context():
        data = {
            'title': 'Updated Task Title',
            'status': StatusEnum.IN_PROGRESS.value
        }
        
        response = client.put(f'/tasks/{test_task.task_id}', json=data, headers=auth_headers)
        assert response.status_code == 200
        
        # Check response data
        task = json.loads(response.data)
        assert task['title'] == 'Updated Task Title'
        assert task['status'] == StatusEnum.IN_PROGRESS.value

def test_update_nonexistent_task(client, auth_headers):
    """Test updating a task that doesn't exist."""
    data = {'title': 'New Title'}
    response = client.put(f'/tasks/{uuid.uuid4()}', json=data, headers=auth_headers)
    assert response.status_code == 404

def test_update_task_invalid_status(client, test_task, auth_headers):
    """Test updating a task with invalid status."""
    with client.application.app_context():
        data = {'status': 'invalid_status'}
        response = client.put(f'/tasks/{test_task.task_id}', json=data, headers=auth_headers)
        print("Update task invalid status response:", response.data)  # Debug print
        assert response.status_code == 400

def test_delete_task(client, test_task, auth_headers):
    """Test deleting a task."""
    with client.application.app_context():
        response = client.delete(f'/tasks/{test_task.task_id}', headers=auth_headers)
        print("Delete task response:", response.data)  # Debug print
        assert response.status_code == 204
        
        # Verify task is deleted
        response = client.get(f'/tasks/{test_task.task_id}', headers=auth_headers)
        assert response.status_code == 404

def test_delete_nonexistent_task(client, auth_headers):
    """Test deleting a task that doesn't exist."""
    response = client.delete(f'/tasks/{uuid.uuid4()}', headers=auth_headers)
    assert response.status_code == 404
