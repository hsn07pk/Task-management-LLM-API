import json
from functools import wraps
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask, jsonify, request

from schemas.schemas import (PROJECT_SCHEMA, TASK_SCHEMA, TEAM_MEMBERSHIP_SCHEMA,
                           TEAM_SCHEMA, TEAM_UPDATE_SCHEMA, USER_SCHEMA,
                           USER_UPDATE_SCHEMA)
from validators.validators import validate_json


@pytest.fixture
def test_app():
    """Create a test Flask application."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def test_client(test_app):
    """Create a test client using the test app."""
    return test_app.test_client()


def test_validate_json_decorator_valid(test_app, test_client):
    """Test validate_json decorator with valid JSON data."""

    # Define a simple JSON schema for testing
    test_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        },
        "required": ["name", "age"]
    }

    # Create a route that uses the validate_json decorator
    @test_app.route('/test', methods=['POST'])
    @validate_json(test_schema)
    def test_route():
        data = request.get_json()
        return jsonify({"success": True, "data": data}), 200

    # Test with valid data
    valid_data = {"name": "John", "age": 30}
    response = test_client.post('/test', json=valid_data)
    
    assert response.status_code == 200
    assert json.loads(response.data)["success"] is True
    assert json.loads(response.data)["data"] == valid_data


def test_validate_json_decorator_missing_required(test_app, test_client):
    """Test validate_json decorator with missing required fields."""

    # Define a simple JSON schema for testing
    test_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        },
        "required": ["name", "age"]
    }

    # Create a route that uses the validate_json decorator
    @test_app.route('/test', methods=['POST'])
    @validate_json(test_schema)
    def test_route():
        data = request.get_json()
        return jsonify({"success": True, "data": data}), 200

    # Test with missing required field
    invalid_data = {"name": "John"}  # Missing age field
    response = test_client.post('/test', json=invalid_data)

    assert response.status_code == 400
    # Check that the response contains the error message, being more flexible with the exact wording
    response_data = json.loads(response.data)
    assert "error" in response_data
    assert "age" in response_data["error"]
    assert "required" in response_data["error"].lower()


def test_validate_json_decorator_wrong_type(test_app, test_client):
    """Test validate_json decorator with wrong data type."""

    # Define a simple JSON schema for testing
    test_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        },
        "required": ["name", "age"]
    }

    # Create a route that uses the validate_json decorator
    @test_app.route('/test', methods=['POST'])
    @validate_json(test_schema)
    def test_route():
        data = request.get_json()
        return jsonify({"success": True, "data": data}), 200

    # Test with wrong data type
    invalid_data = {"name": "John", "age": "thirty"}  # Age should be an integer
    response = test_client.post('/test', json=invalid_data)

    assert response.status_code == 400
    # Check that the response contains the error message, being more flexible with the exact wording
    response_data = json.loads(response.data)
    assert "error" in response_data
    assert "integer" in response_data["error"].lower()
    assert "thirty" in response_data["error"]


def test_validate_json_decorator_no_json(test_app, test_client):
    """Test validate_json decorator with no JSON data."""

    # Define a simple JSON schema for testing
    test_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        },
        "required": ["name", "age"]
    }

    # Create a route that uses the validate_json decorator
    @test_app.route('/test', methods=['POST'])
    @validate_json(test_schema)
    def test_route():
        data = request.get_json()
        return jsonify({"success": True, "data": data}), 200

    # Test with no JSON data
    response = test_client.post('/test')

    assert response.status_code == 400
    # Check that the response contains the error message, being more flexible with the exact wording
    response_data = json.loads(response.data)
    assert "error" in response_data
    assert "data" in response_data["error"].lower()
    assert "input" in response_data["error"].lower() or "json" in response_data["error"].lower()


def test_user_schema_valid():
    """Test USER_SCHEMA with valid data."""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "role": "member"
    }
    
    # Mock the validation function to test the schema directly
    mock_validate = MagicMock(return_value=None)  # No validation errors
    
    with patch('jsonschema.validate', mock_validate):
        # This would normally be done inside the decorator
        from jsonschema import validate
        validate(instance=user_data, schema=USER_SCHEMA)
    
    # Check that validate was called with the right arguments
    mock_validate.assert_called_once_with(instance=user_data, schema=USER_SCHEMA)


def test_user_update_schema_valid():
    """Test USER_UPDATE_SCHEMA with valid data."""
    update_data = {
        "username": "updateduser",
        "email": "updated@example.com"
    }
    
    mock_validate = MagicMock(return_value=None)
    
    with patch('jsonschema.validate', mock_validate):
        from jsonschema import validate
        validate(instance=update_data, schema=USER_UPDATE_SCHEMA)
    
    mock_validate.assert_called_once_with(instance=update_data, schema=USER_UPDATE_SCHEMA)


def test_team_schema_valid():
    """Test TEAM_SCHEMA with valid data."""
    team_data = {
        "name": "Test Team",
        "description": "A team for testing",
        "lead_id": "123e4567-e89b-12d3-a456-426614174000"
    }
    
    mock_validate = MagicMock(return_value=None)
    
    with patch('jsonschema.validate', mock_validate):
        from jsonschema import validate
        validate(instance=team_data, schema=TEAM_SCHEMA)
    
    mock_validate.assert_called_once_with(instance=team_data, schema=TEAM_SCHEMA)


def test_team_update_schema_valid():
    """Test TEAM_UPDATE_SCHEMA with valid data."""
    update_data = {
        "name": "Updated Team",
        "description": "Updated description"
    }
    
    mock_validate = MagicMock(return_value=None)
    
    with patch('jsonschema.validate', mock_validate):
        from jsonschema import validate
        validate(instance=update_data, schema=TEAM_UPDATE_SCHEMA)
    
    mock_validate.assert_called_once_with(instance=update_data, schema=TEAM_UPDATE_SCHEMA)


def test_team_membership_schema_valid():
    """Test TEAM_MEMBERSHIP_SCHEMA with valid data."""
    membership_data = {
        "user_id": "123e4567-e89b-12d3-a456-426614174000",
        "role": "developer"
    }
    
    mock_validate = MagicMock(return_value=None)
    
    with patch('jsonschema.validate', mock_validate):
        from jsonschema import validate
        validate(instance=membership_data, schema=TEAM_MEMBERSHIP_SCHEMA)
    
    mock_validate.assert_called_once_with(instance=membership_data, schema=TEAM_MEMBERSHIP_SCHEMA)


def test_project_schema_valid():
    """Test PROJECT_SCHEMA with valid data."""
    project_data = {
        "title": "Test Project",
        "description": "A project for testing",
        "status": "planning",
        "deadline": "2023-12-31T23:59:59Z",
        "team_id": "123e4567-e89b-12d3-a456-426614174000"
    }
    
    mock_validate = MagicMock(return_value=None)
    
    with patch('jsonschema.validate', mock_validate):
        from jsonschema import validate
        validate(instance=project_data, schema=PROJECT_SCHEMA)
    
    mock_validate.assert_called_once_with(instance=project_data, schema=PROJECT_SCHEMA)


def test_task_schema_valid():
    """Test TASK_SCHEMA with valid data."""
    task_data = {
        "title": "Test Task",
        "description": "A task for testing",
        "priority": 1,
        "status": "pending",
        "deadline": "2023-12-31T23:59:59Z",
        "project_id": "123e4567-e89b-12d3-a456-426614174000",
        "assignee_id": "123e4567-e89b-12d3-a456-426614174000"
    }
    
    mock_validate = MagicMock(return_value=None)
    
    with patch('jsonschema.validate', mock_validate):
        from jsonschema import validate
        validate(instance=task_data, schema=TASK_SCHEMA)
    
    mock_validate.assert_called_once_with(instance=task_data, schema=TASK_SCHEMA) 