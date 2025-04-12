from flask import jsonify


def handle_error(message, status_code):
    """
    Handle errors by returning a JSON response with a status code.

    Args:
        message (str): The error message.
        status_code (int): The HTTP status code.

    Returns:
        Response: A Flask JSON response object.
    """
    return jsonify({"error": message}), status_code


def handle_exception(exception):
    """
    Handle exceptions by returning a generic 500 error response.

    Args:
        exception (Exception): The exception to handle.

    Returns:
        Response: A Flask JSON response object.
    """
    return jsonify({"error": "Internal server error", "message": str(exception)}), 500
