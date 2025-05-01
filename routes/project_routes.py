from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from extentions.extensions import cache
from models import User
from schemas.schemas import PROJECT_SCHEMA, PROJECT_UPDATE_SCHEMA
from services.project_services import ProjectService
from utils.error_handlers import handle_error, handle_exception
from utils.hypermedia.project_hypermedia import (
    add_project_hypermedia_links,
    generate_projects_collection_links
)
from validators.validators import validate_json

# Define the Blueprint
project_bp = Blueprint("project_routes", __name__, url_prefix="/projects")

@project_bp.route("/", methods=["POST"])
@jwt_required()
@validate_json(PROJECT_SCHEMA)
def create_project():
    """Create a new project with hypermedia links."""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if not current_user:
            return handle_error("Current user not found", 404)

        data = request.get_json()
        new_project = ProjectService.create_project(data)

        # Invalidate cached project lists for this user
        cache.delete(f"projects_{current_user_id}")

        # Add hypermedia links
        project_dict = add_project_hypermedia_links(new_project.to_dict())
        return jsonify(project_dict), 201
    except ValueError as e:
        return handle_error(str(e), 400)
    except Exception as e:
        return handle_exception(e)

@project_bp.route("/<project_id>", methods=["GET"])
@jwt_required()
@cache.cached(timeout=300, key_prefix=lambda: f"project_{get_jwt_identity()}_{request.view_args['project_id']}")
def get_project(project_id):
    """Retrieve a specific project by ID with hypermedia links."""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if not current_user:
            return handle_error("Current user not found", 404)

        project = ProjectService.get_project(project_id)
        if not project:
            return handle_error("Project not found", 404)

        project_dict = add_project_hypermedia_links(project.to_dict())
        return jsonify(project_dict), 200
    except Exception as e:
        return handle_exception(e)

@project_bp.route("/<project_id>", methods=["PUT"])
@jwt_required()
@validate_json(PROJECT_UPDATE_SCHEMA)
def update_project(project_id):
    """Update an existing project and return with hypermedia links."""
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

        # Invalidate caches
        cache.delete(f"project_{current_user_id}_{project_id}")
        cache.delete(f"projects_{current_user_id}")

        project_dict = add_project_hypermedia_links(updated_project.to_dict())
        return jsonify(project_dict), 200
    except ValueError as e:
        return handle_error(str(e), 400)
    except Exception as e:
        return handle_exception(e)

@project_bp.route("/<project_id>", methods=["DELETE"])
@jwt_required()
def delete_project(project_id):
    """Delete a project and return navigation hypermedia links."""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if not current_user:
            return handle_error("Current user not found", 404)

        project = ProjectService.get_project(project_id)
        if not project:
            return handle_error("Project not found", 404)

        ProjectService.delete_project(project)

        # Invalidate caches
        cache.delete(f"project_{current_user_id}_{project_id}")
        cache.delete(f"projects_{current_user_id}")

        response = {
            "message": "Project deleted successfully",
            "_links": generate_projects_collection_links()
        }
        return jsonify(response), 200
    except Exception as e:
        return handle_exception(e)


@project_bp.route("/", methods=["GET"])
@jwt_required()
@cache.cached(timeout=300, key_prefix=lambda: f"projects_{get_jwt_identity()}")
def get_all_projects():
    """Fetch all projects."""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if not current_user:
            return handle_error("Current user not found", 404)

        projects = ProjectService.fetch_all_projects()

        # Structure the response with hypermedia at collection level only
        response = {
            "projects": [],
            "_links": generate_projects_collection_links()
        }

        # Add projects to the response without individual hypermedia links
        for project in projects:
            if hasattr(project, 'to_dict'):
                response["projects"].append(project.to_dict())
            elif isinstance(project, dict):
                response["projects"].append(project)
            else:
                # Skip or handle unexpected types
                continue

        return jsonify(response), 200
    except Exception as e:
        return handle_exception(e)
