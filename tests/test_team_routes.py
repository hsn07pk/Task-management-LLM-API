# test_team_routes.py
import pytest
from datetime import datetime, timedelta
import json
import uuid
from models import StatusEnum, PriorityEnum

def test_create_team(client, test_user):
    # Log in to get the token
    login_data = {'email': 'test@example.com', 'password': 'test_hash'}
    login_response = client.post('/login', json=login_data)
    token = login_response.json['access_token']
    
    data = {'name': 'Dev Team', 'lead_id': str(test_user.user_id)}
    response = client.post(
        '/teams',
        json=data,
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 201

def test_add_member(client, test_team, test_user):
    data = {'user_id': str(test_user.user_id), 'role': 'member'}
    response = client.post(f'/teams/{test_team.team_id}/members', json=data)
    assert response.status_code == 201
    
def test_update_team(client, test_team):
    data = {"name": "Updated Team Name"}
    response = client.put(f'/teams/{test_team.team_id}', json=data)
    assert response.status_code == 200
    assert response.json['name'] == "Updated Team Name"

def test_delete_team(client, test_team):
    response = client.delete(f'/teams/{test_team.team_id}')
    assert response.status_code == 200
    response = client.get(f'/teams/{test_team.team_id}')
    assert response.status_code == 404

def test_add_duplicate_member(client, test_team, test_user):
    data = {"user_id": str(test_user.user_id), "role": "member"}
    response = client.post(f'/teams/{test_team.team_id}/members', json=data)
    assert response.status_code == 400
    
def test_get_nonexistent_team(client):
    response = client.get(f'/teams/{uuid.uuid4()}')
    assert response.status_code == 404

def test_add_member_invalid_role(client, test_team, test_user):
    data = {"user_id": str(test_user.user_id), "role": "invalid_role"}
    response = client.post(f'/teams/{test_team.team_id}/members', json=data)
    assert response.status_code == 400