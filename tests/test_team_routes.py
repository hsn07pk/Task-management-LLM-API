# test_team_routes.py

import pytest
from datetime import datetime, timedelta
import json
import uuid
from models import StatusEnum, PriorityEnum, Team, User, db
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash

@pytest.fixture(scope="session")
def app():
    """
    Fixture to create and configure a Flask app for testing with PostgreSQL.

    This fixture sets up the Flask application for testing purposes, configuring it 
    with a test-specific database URI, testing mode, and a secret key for JWT authentication.

    Returns:
        app (Flask): The configured Flask application for testing.
    """
    from app import create_app
    app = create_app()
    return app

@pytest.fixture(scope="function")
def client(app):
    """
    Fixture to create a test client for the Flask application.

    This fixture creates a test client that can be used to make requests to the
    Flask application during testing. It also sets up and tears down an application
    context for each test.

    Args:
        app (Flask): The Flask application fixture.

    Returns:
        FlaskClient: A test client for the Flask application.
    """
    with app.test_client() as client:
        with app.app_context():
            yield client

# Fixture to create a test user
@pytest.fixture(scope="function")
def test_user(app):
    """
    Fixture to create a test user.
    
    This fixture creates a new test user in the database. The user is committed
    to the database and returned as a dictionary for use in tests.
    
    Args:
        app (Flask): The Flask application instance.
        
    Returns:
        dict: A dictionary containing the user's ID and other information.
    """
    with app.app_context():
        # Generate unique identifiers for this test run
        unique_id = str(uuid.uuid4())[:8]
        
        # Hash the password
        password_hash = generate_password_hash('password123')
        
        user = User(
            username=f'testuser_{unique_id}',
            email=f'test_{unique_id}@example.com',
            password_hash=password_hash,
            role='user'
        )
        db.session.add(user)
        db.session.commit()
        
        # Return a dictionary with user information to avoid session issues
        return {
            'id': str(user.user_id),
            'username': user.username,
            'email': user.email,
            'role': user.role
        }

# Fixture to create a second test user for membership tests
@pytest.fixture(scope="function")
def test_member(app):
    """
    Fixture to create a test user for team membership.
    
    This fixture creates a new test user in the database specifically for adding
    to teams. The user is committed to the database and returned as a dictionary
    for use in tests.
    
    Args:
        app (Flask): The Flask application instance.
        
    Returns:
        dict: A dictionary containing the user's ID and other information.
    """
    with app.app_context():
        # Generate unique identifiers for this test run
        unique_id = str(uuid.uuid4())[:8]
        
        # Hash the password
        password_hash = generate_password_hash('memberpass123')
        
        user = User(
            username=f'testmember_{unique_id}',
            email=f'member_{unique_id}@example.com',
            password_hash=password_hash,
            role='user'
        )
        db.session.add(user)
        db.session.commit()
        
        # Return a dictionary with user information to avoid session issues
        return {
            'id': str(user.user_id),
            'username': user.username,
            'email': user.email,
            'role': user.role
        }

# Fixture to create a test team
@pytest.fixture(scope="function")
def test_team(app, test_user):
    """
    Fixture to create a test team.
    
    This fixture creates a new test team in the database, with the test user
    as the team lead. The team is committed to the database and returned as
    a dictionary for use in tests.
    
    Args:
        app (Flask): The Flask application instance.
        test_user (dict): The user to be assigned as the team lead.
        
    Returns:
        dict: A dictionary containing the team's ID and other information.
    """
    with app.app_context():
        team = Team(
            name='Test Team',
            lead_id=uuid.UUID(test_user['id'])
        )
        db.session.add(team)
        db.session.commit()
        
        # Return a dictionary with team information to avoid session issues
        return {
            'id': str(team.team_id),
            'name': team.name,
            'lead_id': str(team.lead_id)
        }

# Fixture to create authentication headers
@pytest.fixture(scope="function")
def auth_headers(app, test_user):
    """
    Fixture to generate authorization headers with JWT token for the test user.
    
    This fixture creates a JWT token for the test user and returns it in the
    authorization headers format for use in making authenticated requests.
    
    Args:
        app (Flask): The Flask application instance.
        test_user (dict): The user for whom to create the token.
        
    Returns:
        dict: The authorization headers containing the JWT token.
    """
    with app.app_context():
        token = create_access_token(identity=test_user['id'])
        return {'Authorization': f'Bearer {token}'}

# Test case to create a team
@pytest.mark.parametrize('team_name, lead_id_param', [('Dev Team', 'lead_id')])
def test_create_team(client, team_name, lead_id_param, auth_headers, test_user):
    """
    Test the creation of a new team via the API.

    This test verifies that a team can be created successfully by sending
    a POST request with the necessary data. It checks that the response
    contains a `team_id` and the status code is 201 (Created).

    Args:
        client: The Flask test client used for making API requests.
        team_name (str): The name of the team to be created.
        lead_id_param (str): Parameter to determine the lead_id to use.
        auth_headers (dict): The authorization headers containing the JWT token.
        test_user (dict): The test user to use as the team lead.

    Asserts:
        - The status code of the response is 201 (Created).
        - The response contains the `team_id`.
    """
    # Use the test_user's ID as the lead_id
    lead_id = test_user['id']
    
    # Prepare data for team creation
    data = {'name': team_name, 'lead_id': lead_id}
    
    # Make POST request to create the team
    response = client.post('/teams', json=data, headers=auth_headers)

    # Assert the team was created successfully
    assert response.status_code == 201, f"Expected status code 201, got {response.status_code}"
    assert 'team_id' in json.loads(response.data), "Response does not contain team_id"

# Test case to add a member to a team
def test_add_member(client, test_team, test_member, auth_headers):
    """
    Test adding a member to a team via the API.

    This test ensures that a user can be added to an existing team by
    sending a POST request with the user's ID and their role. The test
    checks if the member is successfully added and if the response
    status code is 201 (Created).

    Args:
        client: The Flask test client used for making API requests.
        test_team (dict): The test team to which the member will be added.
        test_member (dict): The test user to be added as a member.
        auth_headers (dict): The authorization headers containing the JWT token.

    Asserts:
        - The status code of the response is 201 (Created).
        - The response contains a success message.
    """
    # Prepare data for adding a member
    data = {
        'user_id': test_member['id'],
        'role': 'developer'
    }
    
    # Make POST request to add the member
    response = client.post(f'/teams/{test_team["id"]}/members', json=data, headers=auth_headers)
    
    # Assert the member was added successfully
    assert response.status_code == 201, f"Expected status code 201, got {response.status_code}"
    response_data = json.loads(response.data)
    assert 'message' in response_data, "Response does not contain a message"
    assert 'success' in response_data['message'].lower(), "Message does not indicate success"
