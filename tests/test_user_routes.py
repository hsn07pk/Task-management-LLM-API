import pytest
import json
import uuid

def test_create_team(client, test_user):
    """Test creating a new team."""
    data = {
        'name': 'Test Team',
        'description': 'A team for testing',
        'lead_id': str(test_user.user_id)
    }
    
    response = client.post('/teams', json=data)
    print("Create team response:", response.data)  # Debug print
    assert response.status_code == 201
    
    # Check response data
    response_data = json.loads(response.data)
    assert response_data['name'] == 'Test Team'
    assert response_data['description'] == 'A team for testing'
    assert response_data['lead_id'] == str(test_user.user_id)
    assert 'team_id' in response_data

def test_create_team_missing_required_fields(client):
    """Test creating a team with missing required fields."""
    data = {
        'description': 'Incomplete team'
    }
    
    response = client.post('/teams', json=data)
    assert response.status_code == 400
    assert b'Missing required field' in response.data

def test_create_team_invalid_lead(client):
    """Test creating a team with an invalid lead_id."""
    data = {
        'name': 'Invalid Lead Team',
        'lead_id': str(uuid.uuid4())  # Random UUID that doesn't exist
    }
    
    response = client.post('/teams', json=data)
    assert response.status_code == 404
    assert b'Team lead user not found' in response.data

def test_get_all_teams(client, test_team):
    """Test getting all teams."""
    response = client.get('/teams')
    print("Get all teams response:", response.data)  # Debug print
    assert response.status_code == 200