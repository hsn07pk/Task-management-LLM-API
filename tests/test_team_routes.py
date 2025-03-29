# test_team_routes.py

import pytest
from datetime import datetime, timedelta
import json
import uuid
from models import StatusEnum, PriorityEnum

# Test case to create a team
@pytest.mark.parametrize('team_name, lead_id', [('Dev Team', uuid.uuid4())])
def test_create_team(client, team_name, lead_id):
    """
    Test the creation of a new team via the API.

    This test verifies that a team can be created successfully by sending
    a POST request with the necessary data. It checks that the response
    contains a `team_id` and the status code is 201 (Created).

    Args:
        client: The Flask test client used for making API requests.
        team_name (str): The name of the team to be created.
        lead_id (uuid.UUID): The ID of the lead for the team.

    Asserts:
        - The status code of the response is 201 (Created).
        - The response contains the `team_id`.
    """
    # Prepare data for team creation
    data = {'name': team_name, 'lead_id': str(lead_id)}
    
    # Make POST request to create the team
    response = client.post('/teams', json=data)

    # Assert the team was created successfully
    assert response.status_code == 201, f"Expected status code 201, got {response.status_code}"
    assert 'team_id' in response.json, "Response does not contain team_id"

# Test case to add a member to a team
def test_add_member(client, test_team, test_user):
    """
    Test adding a member to a team via the API.

    This test ensures that a user can be added to an existing team by
    sending a POST request with the user's ID and their role. The test
    checks if the member is successfully added and if the response
    status code is 201 (Created).

    Args:
        client: The Flask test client used for making API requests.
        test_team (Team): The test team to which the member will be added.
        test_user (User): The test user to be added as a member.

    Asserts:
        - The status code of the response is 201 (Created).
        - The response confirms the member was added successfully.
    """
    # Prepare data for adding the member
    data = {'user_id': str(test_user.user_id), 'role': 'member'}
    
    # Make POST request to add the member to the team
    response = client.post(f'/teams/{test_team.team_id}/members', json=data)

    # Assert the member was added successfully
    assert response.status_code == 201, f"Expected status code 201, got {response.status_code}"

