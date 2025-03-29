from uuid import UUID

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extentions.extensions import cache
from models import Project, Team, User, db
from schemas.schemas import PROJECT_SCHEMA
from validators.validators import validate_json

# Create a new Blueprint for project-related routes
project_bp = Blueprint("project_routes", __name__)

# ------------------ ERROR HANDLERS ------------------


@project_bp.errorhandler(400)
def bad_request(error):
    """
    Handles 400 Bad Request errors.

    Args:
        error: The error object passed when a 400 error is encountered.

    Returns:
        A JSON response with the error message and a 400 status code.
    """
    return jsonify({"error": "Bad Request", "message": str(error)}), 400


@project_bp.errorhandler(404)
def not_found(error):
    """
    Handles 404 Not Found errors.

    Args:
        error: The error object passed when a 404 error is encountered.

    Returns:
        A JSON response with the error message and a 404 status code.
    """
    return jsonify({"error": "Not Found", "message": str(error)}), 404


@project_bp.errorhandler(500)
def internal_error(error):
    """
    Handles 500 Internal Server errors.

    Args:
        error: The error object passed when a 500 error is encountered.

    Returns:
        A JSON response with the error message and a 500 status code.
    """
    return jsonify({"error": "Internal Server Error", "message": str(error)}), 500


# ------------------ PROJECT ROUTES ------------------


@project_bp.route("/projects", methods=["POST"])
@jwt_required()
@validate_json(PROJECT_SCHEMA)
def create_project():
    """
    Create a new project associated with a team.

    This route allows users to create a new project by providing a title, description,
    team ID, and optional category ID. The request body should follow the PROJECT_SCHEMA.

    Returns:
        A JSON response with the created project's details and a 201 status code if successful,
        or an error message with an appropriate HTTP status code.
    """
    try:
        # Get JSON data from the request body
        data = request.get_json()

        # Check if current user exists
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if not current_user:
            return jsonify({"error": "Current user not found"}), 404

        # Convert team_id from string to UUID and validate
        try:
            team_id = UUID(data["team_id"])
        except (ValueError, KeyError) as e:
            return jsonify({"error": "Invalid team_id", "message": str(e)}), 400

        # Validate if the team exists in the database
        team = Team.query.get(team_id)
        if not team:
            return jsonify({"error": "Team not found"}), 404

        # Handle optional category_id
        category_id = None
        if "category_id" in data and data["category_id"]:
            try:
                category_id = UUID(data["category_id"])
            except ValueError as e:
                return jsonify({"error": "Invalid category_id format", "message": str(e)}), 400

        # Create a new Project object and populate it with the request data
        new_project = Project(
            title=data["title"],
            description=data.get("description"),
            team_id=team_id,
            category_id=category_id,
        )

        # Add the new project to the database and commit the changes
        db.session.add(new_project)
        db.session.commit()

        # Return the created project details
        return jsonify(new_project.to_dict()), 201

    except KeyError as e:
        # Handle missing required fields
        return (
            jsonify({"error": "Missing required field", "message": f"Field {str(e)} is required"}),
            400,
        )
    except ValueError as e:
        # Handle invalid UUID format error
        return jsonify({"error": "Invalid UUID format", "message": str(e)}), 400
    except Exception as e:
        # Rollback the session in case of any other errors
        db.session.rollback()
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


@project_bp.route("/projects/<uuid:project_id>", methods=["GET"])
@jwt_required()
@cache.cached(timeout=60)
def get_project(project_id):
    """
    Get the details of a specific project.

    Args:
        project_id (uuid): The ID of the project to retrieve.

    Returns:
        A JSON response with the project's details and a 200 status code if found,
        or an error message with a 404 status code if the project does not exist.
    """
    try:
        # Check if current user exists
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if not current_user:
            return jsonify({"error": "Current user not found"}), 404

        # Retrieve the project by its ID
        project = Project.query.get(project_id)

        # Check if the project exists
        if not project:
            return jsonify({"error": "Project not found"}), 404

        # Return the project details
        return jsonify(project.to_dict()), 200
    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


@project_bp.route("/projects/<uuid:project_id>", methods=["PUT"])
@jwt_required()
@validate_json(PROJECT_SCHEMA)
def update_project(project_id):
    """
    Update the details of an existing project.

    Args:
        project_id (uuid): The ID of the project to update.

    Returns:
        A JSON response with the updated project details and a 200 status code if successful,
        or an error message with a 404 status code if the project does not exist.
    """
    try:
        # Check if current user exists
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if not current_user:
            return jsonify({"error": "Current user not found"}), 404

        # Retrieve the project by its ID
        project = Project.query.get(project_id)

        # Check if the project exists
        if not project:
            return jsonify({"error": "Project not found"}), 404

        # Get the updated data from the request body
        data = request.get_json()

        # Update the project details based on the provided data
        if "title" in data:
            project.title = data["title"]

        if "description" in data:
            project.description = data["description"]

        if "team_id" in data:
            try:
                team_id = UUID(data["team_id"])
                # Verify team exists
                team = Team.query.get(team_id)
                if not team:
                    return jsonify({"error": "Team not found"}), 404
                project.team_id = team_id
            except ValueError as e:
                return jsonify({"error": "Invalid team_id format", "message": str(e)}), 400

        if "category_id" in data:
            if data["category_id"]:
                try:
                    category_id = UUID(data["category_id"])
                    project.category_id = category_id
                except ValueError as e:
                    return jsonify({"error": "Invalid category_id format", "message": str(e)}), 400
            else:
                project.category_id = None

        # Commit the changes to the database
        db.session.commit()

        # Return the updated project details
        return jsonify(project.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


@project_bp.route("/projects/<uuid:project_id>", methods=["DELETE"])
@jwt_required()
def delete_project(project_id):
    """
    Delete an existing project.

    Args:
        project_id (uuid): The ID of the project to delete.

    Returns:
        A JSON response confirming deletion and a 200 status code if successful,
        or an error message with a 404 status code if the project does not exist.
    """
    try:
        # Check if current user exists
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if not current_user:
            return jsonify({"error": "Current user not found"}), 404

        # Retrieve the project by its ID
        project = Project.query.get(project_id)

        # Check if the project exists
        if not project:
            return jsonify({"error": "Project not found"}), 404

        # Delete the project from the database
        db.session.delete(project)
        db.session.commit()

        # Return a success message
        return jsonify({"message": "Project deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
