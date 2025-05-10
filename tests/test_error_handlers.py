import json

import pytest

from utils.error_handlers import handle_error, handle_exception


def test_handle_error():
    """Test the handle_error function."""
    # Test with a simple error message
    response, status_code = handle_error("Test error message", 400)
    assert status_code == 400

    # Convert response to JSON
    response_data = json.loads(response.get_data(as_text=True))
    assert "error" in response_data
    assert response_data["error"] == "Test error message"

    # Test with different status code
    response, status_code = handle_error("Not found", 404)
    assert status_code == 404
    response_data = json.loads(response.get_data(as_text=True))
    assert response_data["error"] == "Not found"

    # Test with empty message
    response, status_code = handle_error("", 400)
    response_data = json.loads(response.get_data(as_text=True))
    assert response_data["error"] == ""


def test_handle_exception():
    """Test the handle_exception function."""
    # Test with a simple exception
    exception = ValueError("Test exception message")
    response, status_code = handle_exception(exception)
    assert status_code == 500

    # Convert response to JSON
    response_data = json.loads(response.get_data(as_text=True))
    assert "error" in response_data
    assert response_data["error"] == "Internal server error"
    assert "message" in response_data
    assert response_data["message"] == "Test exception message"

    # Test with a different exception type
    exception = KeyError("Missing key")
    response, status_code = handle_exception(exception)
    assert status_code == 500
    response_data = json.loads(response.get_data(as_text=True))
    assert response_data["message"] == "'Missing key'"

    # Test with Exception base class
    exception = Exception("Generic error")
    response, status_code = handle_exception(exception)
    assert status_code == 500
    response_data = json.loads(response.get_data(as_text=True))
    assert response_data["message"] == "Generic error"
