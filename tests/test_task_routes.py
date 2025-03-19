import pytest
from datetime import datetime, timedelta
import json
import uuid
from models import StatusEnum, PriorityEnum

def test_create_task(client, test_user, test_project):
    """Test creating a new task."""
    data = {
        'title': 'New Test Task',
        'description': 'Description for new test task',
        'priority': PriorityEnum.MEDIUM.value,
        'status': StatusEnum.PENDING.value,
        'project_id': str(test_project.project_id),
        'assignee_id': str(test_user.user_id),
        'deadline': (datetime.utcnow() + timedelta(days=7)).isoformat()
    }
    
    response = client.post('/tasks', json=data)
    print("Create task response:", response.data)  # Debug print
    assert response.status_code == 201
    
    # Check response data
    response_data = json.loads(response.data)
    assert response_data['title'] == 'New Test Task'
    assert response_data['description'] == 'Description for new test task'
    assert response_data['status'] == StatusEnum.PENDING.value
    assert 'task_id' in response_data

def test_create_task_missing_required_fields(client, test_user):
    # Log in and get token
    login_response = client.post('/login', json={'email': test_user.email, 'password': 'test_hash'})
    token = login_response.json['access_token']
    
    data = {'description': 'Missing title'}
    response = client.post(
        '/tasks',
        json=data,
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400

def test_get_all_tasks(client, test_task):
    """Test getting all tasks."""
    response = client.get('/tasks')
    print("Get all tasks response:", response.data)  # Debug print
    assert response.status_code == 200
    
    # Check response data
    tasks = json.loads(response.data)
    assert isinstance(tasks, list)
    assert len(tasks) > 0
    assert tasks[0]['title'] == 'Test Task'

def test_get_tasks_with_filters(client, test_task):
    """Test getting tasks with filters."""
    # Test project_id filter
    response = client.get(f'/tasks?project_id={test_task.project_id}')
    print("Get tasks with filters response:", response.data)  # Debug print
    assert response.status_code == 200
    tasks = json.loads(response.data)
    assert len(tasks) == 1
    assert tasks[0]['project_id'] == str(test_task.project_id)

    # Test assignee_id filter
    response = client.get(f'/tasks?assignee_id={test_task.assignee_id}')
    assert response.status_code == 200
    tasks = json.loads(response.data)
    assert len(tasks) == 1
    assert tasks[0]['assignee_id'] == str(test_task.assignee_id)

    # Test status filter
    response = client.get(f'/tasks?status={StatusEnum.PENDING.value}')
    assert response.status_code == 200
    tasks = json.loads(response.data)
    assert all(task['status'] == StatusEnum.PENDING.value for task in tasks)

def test_get_single_task(client, test_task):
    """Test getting a single task."""
    response = client.get(f'/tasks/{test_task.task_id}')
    assert response.status_code == 200
    
    # Check response data
    task = json.loads(response.data)
    assert task['task_id'] == str(test_task.task_id)
    assert task['title'] == test_task.title

def test_get_nonexistent_task(client):
    response = client.get(f'/tasks/{uuid.uuid4()}')  # Confirm this is the correct endpoint and method
    assert response.status_code == 404

def test_update_task(client, test_task):
    """Test updating a task."""
    data = {
        'title': 'Updated Task Title',
        'status': StatusEnum.IN_PROGRESS.value
    }
    
    response = client.put(f'/tasks/{test_task.task_id}', json=data)
    assert response.status_code == 200
    
    # Check response data
    task = json.loads(response.data)
    assert task['title'] == 'Updated Task Title'
    assert task['status'] == StatusEnum.IN_PROGRESS.value

def test_update_nonexistent_task(client, test_user):
    client.post('/login', data={'email': test_user.email, 'password': 'Testpass123!'})
    data = {'title': 'New Title'}
    response = client.put(f'/tasks/{uuid.uuid4()}', json=data)
    assert response.status_code == 404

def test_update_task_invalid_status(client, test_task):
    data = {'status': 'invalid_status'}
    response = client.put(f'/tasks/{test_task.task_id}', json=data)
    assert response.status_code == 400 

def test_delete_task(client, test_task):
    """Test deleting a task."""
    response = client.delete(f'/tasks/{test_task.task_id}')
    print("Delete task response:", response.data)  # Debug print
    assert response.status_code == 204
    
    # Verify task is deleted
    response = client.get(f'/tasks/{test_task.task_id}')
    assert response.status_code == 404

def test_delete_nonexistent_task(client):
    """Test deleting a task that doesn't exist."""
    response = client.delete(f'/tasks/{uuid.uuid4()}')
    assert response.status_code == 404
