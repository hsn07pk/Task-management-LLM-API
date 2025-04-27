

from flask import Blueprint, jsonify, url_for

# Define the Blueprint
entry_bp = Blueprint("entry_point", __name__)

@entry_bp.route("/", methods=["GET"])
def api_root():
    """
    Entry point for the API. Returns the available routes for unauthenticated users.
    This acts as the starting point for API exploration.
    
    Returns:
        JSON response with available links
    """
    response = {
        "name": "Task Management API",
        "version": "1.0",
        "_links": {
            "self": {"href": url_for("entry_point.api_root", _external=True)},
            "login": {
                "href": url_for("login", _external=True),
                "templated": False,
                "method": "POST",
                "schema": {
                    "type": "object",
                    "properties": {
                        "email": {"type": "string"},
                        "password": {"type": "string"}
                    },
                    "required": ["email", "password"]
                }
            },
            "register": {
                "href": url_for("user_routes.create_user", _external=True),
                "templated": False,
                "method": "POST"
            },
            "documentation": {
                "href": url_for("flasgger.apidocs", _external=True),
                "templated": False,
                "method": "GET"
            }
        }
    }
    return jsonify(response), 200