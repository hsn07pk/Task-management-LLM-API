# test_team_routes.py
import pytest
from datetime import datetime, timedelta
import json
import uuid
from models import StatusEnum, PriorityEnum

def test_create_team(client):
    data = {'name': 'Dev Team', 'lead_id': str(uuid.uuid4())}
    response = client.post('/teams', json=data)
    assert response.status_code == 201
    assert 'team_id' in response.json

def test_add_member(client, test_team, test_user):
    data = {'user_id': str(test_user.user_id), 'role': 'member'}
    response = client.post(f'/teams/{test_team.team_id}/members', json=data)
    assert response.status_code == 201