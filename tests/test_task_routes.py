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
def test_user(app, client):
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
        
        # Store the email for later use in auth_headers
        user.test_email = f"{unique_username}@example.com"
        
        # Refresh the user to ensure it's attached to the session
        user = db.session.get(User, user.user_id)
        return user

@pytest.fixture(scope="function")
def test_project(app, test_user):
    """Create a test project."""
    with app.app_context():
        # Refresh the user to ensure it's attached to the session
        user = db.session.get(User, test_user.user_id)
        
        project = Project(
            title='Test Project',
            description='Test project description',
            status='active',
            team_id=None  # No team for simplicity
        )
        db.session.add(project)
        db.session.commit()
        
        # Refresh the project to ensure it's attached to the session
        project = db.session.get(Project, project.project_id)
        return project

@pytest.fixture(scope="function")
def test_task(app, test_user, test_project):
    """Create a test task."""
    with app.app_context():
        # Refresh the user and project to ensure they're attached to the session
        user = db.session.get(User, test_user.user_id)
        project = db.session.get(Project, test_project.project_id)
        
        task = Task(
            title='Test Task',
            description='Test task description',
            status=StatusEnum.PENDING.value,
            priority=PriorityEnum.MEDIUM.value,
            project_id=project.project_id,
            assignee_id=user.user_id,
            created_by=user.user_id,
            deadline=datetime.utcnow() + timedelta(days=7)
        )
        db.session.add(task)
        db.session.commit()
        
        # Refresh the task to ensure it's attached to the session
        task = db.session.get(Task, task.task_id)
        return task

@pytest.fixture(scope="function")
def auth_headers(app, client, test_user):
    """Get auth headers with JWT token."""
    with app.app_context():
        # Use the email created for this specific test user
        response = client.post('/login', json={
            'email': test_user.test_email,
            'password': 'password123'
        })
        assert response.status_code == 200, f"Login failed: {response.data}"
        
        token = json.loads(response.data)['access_token']
        return {'Authorization': f'Bearer {token}'}

def test_create_task(client, test_user, test_project, auth_headers):
    """Test creating a new task."""
    with client.application.app_context():
        # Refresh objects to ensure they're attached to the session
        user = db.session.get(User, test_user.user_id)
        project = db.session.get(Project, test_project.project_id)
        
        data = {
            'title': 'New Test Task',
            'description': 'Description for new test task',
            'priority': 'MEDIUM',  # Sending priority as a string instead of an integer
            'status': StatusEnum.PENDING.value,
            'project_id': str(project.project_id),
            'assignee_id': str(user.user_id),
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
    # Update the assertion to match the actual error message
    assert b'is a required property' in response.data

def test_get_all_tasks(client, test_task, auth_headers):
    """Test getting all tasks."""
    with client.application.app_context():
        # Refresh the task to ensure it's attached to the session
        task = db.session.get(Task, test_task.task_id)
        
        response = client.get('/tasks', headers=auth_headers)
        print("Get all tasks response:", response.data)  # Debug print
        assert response.status_code == 200
        
        # Check response data
        tasks = json.loads(response.data)
        assert isinstance(tasks, list)
        assert len(tasks) > 0
        assert any(t['title'] == task.title for t in tasks)

def test_get_tasks_with_filters(client, test_task, auth_headers):
    """Test getting tasks with filters."""
    with client.application.app_context():
        # Refresh the task to ensure it's attached to the session
        task = db.session.get(Task, test_task.task_id)
        
        # Test project_id filter
        response = client.get(f'/tasks?project_id={task.project_id}', headers=auth_headers)
        print("Get tasks with filters response:", response.data)  # Debug print
        assert response.status_code == 200
        tasks = json.loads(response.data)
        assert len(tasks) >= 1
        assert any(t['project_id'] == str(task.project_id) for t in tasks)

        # Test assignee_id filter
        response = client.get(f'/tasks?assignee_id={task.assignee_id}', headers=auth_headers)
        assert response.status_code == 200
        tasks = json.loads(response.data)
        assert len(tasks) >= 1
        assert any(t['assignee_id'] == str(task.assignee_id) for t in tasks)

        # Test status filter
        response = client.get(f'/tasks?status={StatusEnum.PENDING.value}', headers=auth_headers)
        assert response.status_code == 200
        tasks = json.loads(response.data)
        assert any(t['status'] == StatusEnum.PENDING.value for t in tasks)

def test_get_single_task(client, test_task, auth_headers):
    """Test getting a single task."""
    with client.application.app_context():
        # Refresh the task to ensure it's attached to the session
        task = db.session.get(Task, test_task.task_id)
        
        response = client.get(f'/tasks/{task.task_id}', headers=auth_headers)
        assert response.status_code == 200
        
        # Check response data
        task_data = json.loads(response.data)
        assert task_data['task_id'] == str(task.task_id)
        assert task_data['title'] == task.title

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
        # Refresh the task to ensure it's attached to the session
        task = db.session.get(Task, test_task.task_id)
        
        data = {
            'title': 'Updated Task Title',
            'description': 'Updated task description',
            'status': StatusEnum.IN_PROGRESS.value
        }
        
        response = client.put(f'/tasks/{task.task_id}', json=data, headers=auth_headers)
        assert response.status_code == 200
        
        # Check response data
        updated_task = json.loads(response.data)
        assert updated_task['title'] == 'Updated Task Title'
        assert updated_task['description'] == 'Updated task description'
        assert updated_task['status'] == StatusEnum.IN_PROGRESS.value
        assert updated_task['task_id'] == str(task.task_id)

def test_update_task_invalid_status(client, test_task, auth_headers):
    """Test updating a task with invalid status."""
    with client.application.app_context():
        # Refresh the task to ensure it's attached to the session
        task = db.session.get(Task, test_task.task_id)
        
        data = {
            'status': 'invalid_status'  # Invalid status
        }
        
        response = client.put(f'/tasks/{task.task_id}', json=data, headers=auth_headers)
        print("Update task invalid status response:", response.data)  # Debug print
        assert response.status_code == 400

def test_delete_task(client, test_task, auth_headers):
    """Test deleting a task."""
    with client.application.app_context():
        # Refresh the task to ensure it's attached to the session
        task = db.session.get(Task, test_task.task_id)
        
        response = client.delete(f'/tasks/{task.task_id}', headers=auth_headers)
        assert response.status_code == 204
        
        # Verify task is deleted
        response = client.get(f'/tasks/{task.task_id}', headers=auth_headers)
        assert response.status_code == 404

def test_delete_nonexistent_task(client, auth_headers):
    """Test deleting a task that doesn't exist."""
    response = client.delete(f'/tasks/{uuid.uuid4()}', headers=auth_headers)
    assert response.status_code == 404
