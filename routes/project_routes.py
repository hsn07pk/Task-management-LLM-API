from uuid import UUID

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extentions.extensions import cache
from models import User, Project, db
from services.project_services import ProjectService
from utils.error_handlers import handle_error, handle_exception
from validators.validators import validate_json
from schemas.schemas import PROJECT_SCHEMA, PROJECT_UPDATE_SCHEMA

# Define the Blueprint
project_bp = Blueprint("project_routes", __name__)

# ------------------ PROJECT ROUTES ------------------

@project_bp.route("/projects", methods=["POST"])
@jwt_required()
@validate_json(PROJECT_SCHEMA)
def create_project():
    """Creates a new project."""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if not current_user:
            return handle_error("Current user not found", 404)

        data = request.get_json()
        new_project = ProjectService.create_project(data)
        return jsonify(new_project.to_dict()), 201

    except ValueError as e:
        return handle_error(str(e), 400)
    except Exception as e:
        return handle_exception(e)


@project_bp.route("/projects/<uuid:project_id>", methods=["GET"])
@jwt_required()
@cache.cached(timeout=60)
def get_project(project_id):
    """Retrieves a specific project by ID."""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if not current_user:
            return handle_error("Current user not found", 404)

        project = ProjectService.get_project(project_id)
        if not project:
            return handle_error("Project not found", 404)

        return jsonify(project.to_dict()), 200

    except Exception as e:
        return handle_exception(e)


@project_bp.route("/projects/<uuid:project_id>", methods=["PUT"])
@jwt_required()
@validate_json(PROJECT_UPDATE_SCHEMA)
def update_project(project_id):
    """Updates an existing project."""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if not current_user:
            return handle_error("Current user not found", 404)

        project = ProjectService.get_project(project_id)
        if not project:
            return handle_error("Project not found", 404)

        data = request.get_json()
        updated_project = ProjectService.update_project(project, data)

        return jsonify(updated_project.to_dict()), 200

    except ValueError as e:
        return handle_error(str(e), 400)
    except Exception as e:
        return handle_exception(e)


@project_bp.route("/projects/<uuid:project_id>", methods=["DELETE"])
@jwt_required()
def delete_project(project_id):
    """Deletes a project."""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if not current_user:
            return handle_error("Current user not found", 404)

        project = ProjectService.get_project(project_id)
        if not project:
            return handle_error("Project not found", 404)

        ProjectService.delete_project(project)

        return jsonify({"message": "Project deleted successfully"}), 200

    except Exception as e:
        return handle_exception(e)


@project_bp.route("/projects", methods=["GET"])
@jwt_required()
@cache.cached(timeout=2)
def get_all_projects():
    """Fetch all projects."""
    try:
        current_user_id = get_jwt_identity()
        print(current_user_id)
        current_user = User.query.get(current_user_id)
        if not current_user:
            return handle_error("Current user not found", 404)

        projects = ProjectService.fetch_all_projects()
        # print(projects)
        return jsonify(projects), 200

    except Exception as e:
        return handle_exception(e)
