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
    response_data = json.loads(response.data)
    assert isinstance(response_data, list)
    assert len(response_data) >= 1
    
    # Check if our test team is in the result
    found = False
    for team in response_data:
        if team['team_id'] == str(test_team.team_id):
            found = True
            assert team['name'] == test_team.name
            break
    assert found, "Test team not found in results"

def test_get_team_details(client, test_team, test_user):
    """Test getting a specific team's details."""
    response = client.get(f'/teams/{test_team.team_id}')
    assert response.status_code == 200
    
    response_data = json.loads(response.data)
    assert response_data['team_id'] == str(test_team.team_id)
    assert response_data['name'] == test_team.name
    assert 'members' in response_data
    
    # Check if the team lead is in the members list
    found = False
    for member in response_data['members']:
        if member['user_id'] == str(test_user.user_id) and member['role'] == 'leader':
            found = True
            break
    assert found, "Team lead not found in team members"

def test_get_nonexistent_team(client):
    """Test getting a team that doesn't exist."""
    random_id = str(uuid.uuid4())
    response = client.get(f'/teams/{random_id}')
    assert response.status_code == 404
    assert b'Team not found' in response.data

def test_get_team_invalid_id(client):
    """Test getting a team with an invalid UUID format."""
    response = client.get('/teams/not-a-uuid')
    assert response.status_code == 400
    assert b'Invalid team_id format' in response.data

def test_update_team(client, test_team):
    """Test updating a team's information."""
    data = {
        'name': 'Updated Team Name',
        'description': 'Updated description'
    }
    
    response = client.put(f'/teams/{test_team.team_id}', json=data)
    assert response.status_code == 200
    
    response_data = json.loads(response.data)
    assert response_data['name'] == 'Updated Team Name'
    assert response_data['description'] == 'Updated description'
    
    # Verify the changes were persisted
    response = client.get(f'/teams/{test_team.team_id}')
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert response_data['name'] == 'Updated Team Name'

def test_update_team_lead(client, test_team, test_user2):
    """Test updating a team's lead."""
    data = {
        'lead_id': str(test_user2.user_id)
    }
    
    response = client.put(f'/teams/{test_team.team_id}', json=data)
    assert response.status_code == 200
    
    response_data = json.loads(response.data)
    assert response_data['lead_id'] == str(test_user2.user_id)
    
    # Verify the changes are reflected in team members
    response = client.get(f'/teams/{test_team.team_id}')
    assert response.status_code == 200
    response_data = json.loads(response.data)
    
    found = False
    for member in response_data['members']:
        if member['user_id'] == str(test_user2.user_id) and member['role'] == 'leader':
            found = True
            break
    assert found, "New team lead not found in team members with leader role"

def test_update_nonexistent_team(client):
    """Test updating a team that doesn't exist."""
    random_id = str(uuid.uuid4())
    data = {'name': 'This team does not exist'}
    
    response = client.put(f'/teams/{random_id}', json=data)
    assert response.status_code == 404
    assert b'Team not found' in response.data

def test_update_team_invalid_lead(client, test_team):
    """Test updating a team with an invalid lead_id."""
    data = {
        'lead_id': str(uuid.uuid4())  # Random UUID that doesn't exist
    }
    
    response = client.put(f'/teams/{test_team.team_id}', json=data)
    assert response.status_code == 404
    assert b'Team lead user not found' in response.data

def test_delete_team(client, test_team2):
    """Test deleting a team."""
    response = client.delete(f'/teams/{test_team2.team_id}')
    assert response.status_code == 204
    
    # Verify team was deleted
    response = client.get(f'/teams/{test_team2.team_id}')
    assert response.status_code == 404
    assert b'Team not found' in response.data

def test_delete_nonexistent_team(client):
    """Test deleting a team that doesn't exist."""
    random_id = str(uuid.uuid4())
    response = client.delete(f'/teams/{random_id}')
    assert response.status_code == 404
    assert b'Team not found' in response.data

# Team membership tests
def test_add_team_member(client, test_team, test_user2):
    """Test adding a member to a team."""
    data = {
        'user_id': str(test_user2.user_id),
        'role': 'member'
    }
    
    response = client.post(f'/teams/{test_team.team_id}/members', json=data)
    assert response.status_code == 201
    
    response_data = json.loads(response.data)
    assert response_data['user_id'] == str(test_user2.user_id)
    assert response_data['team_id'] == str(test_team.team_id)
    assert response_data['role'] == 'member'
    
    # Verify member was added to team
    response = client.get(f'/teams/{test_team.team_id}')
    response_data = json.loads(response.data)
    
    found = False
    for member in response_data['members']:
        if member['user_id'] == str(test_user2.user_id) and member['role'] == 'member':
            found = True
            break
    assert found, "Added user not found in team members"

def test_add_duplicate_team_member(client, test_team, test_user):
    """Test adding a user who is already a member of the team."""
    data = {
        'user_id': str(test_user.user_id),
        'role': 'member'
    }
    
    response = client.post(f'/teams/{test_team.team_id}/members', json=data)
    assert response.status_code == 400
    assert b'User is already a member of this team' in response.data

def test_add_member_invalid_role(client, test_team, test_user3):
    """Test adding a member with an invalid role."""
    data = {
        'user_id': str(test_user3.user_id),
        'role': 'invalid_role'
    }
    
    response = client.post(f'/teams/{test_team.team_id}/members', json=data)
    assert response.status_code == 400
    assert b'Invalid role' in response.data

def test_update_team_member_role(client, test_team, test_user2):
    """Test updating a team member's role."""
    # First, ensure the user is a member
    data = {
        'user_id': str(test_user2.user_id),
        'role': 'member'
    }
    response = client.post(f'/teams/{test_team.team_id}/members', json=data)
    
    # Now update their role
    data = {
        'role': 'admin'
    }
    response = client.put(f'/teams/{test_team.team_id}/members/{test_user2.user_id}', json=data)
    assert response.status_code == 200
    
    response_data = json.loads(response.data)
    assert response_data['role'] == 'admin'
    
    # Verify the role was updated
    response = client.get(f'/teams/{test_team.team_id}')
    response_data = json.loads(response.data)
    
    found = False
    for member in response_data['members']:
        if member['user_id'] == str(test_user2.user_id) and member['role'] == 'admin':
            found = True
            break
    assert found, "Member role was not updated correctly"

def test_update_member_to_leader(client, test_team, test_user2):
    """Test updating a member to the leader role."""
    data = {
        'role': 'leader'
    }
    response = client.put(f'/teams/{test_team.team_id}/members/{test_user2.user_id}', json=data)
    assert response.status_code == 200
    
    # Verify the member is now the leader
    response = client.get(f'/teams/{test_team.team_id}')
    response_data = json.loads(response.data)
    assert response_data['lead_id'] == str(test_user2.user_id)

def test_update_nonexistent_membership(client, test_team):
    """Test updating a user who is not a member of the team."""
    random_id = str(uuid.uuid4())
    data = {
        'role': 'admin'
    }
    
    response = client.put(f'/teams/{test_team.team_id}/members/{random_id}', json=data)
    assert response.status_code == 404
    assert b'User is not a member of this team' in response.data

def test_remove_team_member(client, test_team, test_user3):
    """Test removing a member from a team."""
    # First, add the user to the team
    data = {
        'user_id': str(test_user3.user_id),
        'role': 'member'
    }
    response = client.post(f'/teams/{test_team.team_id}/members', json=data)
    
    # Now remove them
    response = client.delete(f'/teams/{test_team.team_id}/members/{test_user3.user_id}')
    assert response.status_code == 204
    
    # Verify the member was removed
    response = client.get(f'/teams/{test_team.team_id}')
    response_data = json.loads(response.data)
    
    for member in response_data['members']:
        assert member['user_id'] != str(test_user3.user_id), "User was not properly removed from team"

def test_remove_team_leader(client, test_team, test_user):
    """Test attempting to remove a team leader."""
    response = client.delete(f'/teams/{test_team.team_id}/members/{test_user.user_id}')
    assert response.status_code == 400
    assert b'Cannot remove team leader' in response.data

def test_remove_nonexistent_member(client, test_team):
    """Test removing a user who is not a member of the team."""
    random_id = str(uuid.uuid4())
    response = client.delete(f'/teams/{test_team.team_id}/members/{random_id}')
    assert response.status_code == 404
    assert b'User is not a member of this team' in response.data