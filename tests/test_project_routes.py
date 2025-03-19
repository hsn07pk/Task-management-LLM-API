import pytest
import json
from uuid import uuid4
from models import User

def test_create_project_invalid_team(client, test_user):
    data = {
        "title": "Invalid Team Project",
        "team_id": str(uuid4()),
        "description": "Should fail"
    }
    response = client.post('/projects', json=data)
    assert response.status_code == 404

def test_update_project_category(client, test_project, test_category):
    data = {"category_id": str(test_category.category_id)}
    response = client.put(f'/projects/{test_project.project_id}', json=data)
    assert response.status_code == 200
    assert response.json['category_id'] == str(test_category.category_id)