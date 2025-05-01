from flask import Blueprint, jsonify, request, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from extentions.extensions import cache
from models import User
from schemas.schemas import PROJECT_SCHEMA, PROJECT_UPDATE_SCHEMA
from services.project_services import ProjectService
from utils.error_handlers import handle_error, handle_exception
from utils.hypermedia.project_hypermedia import add_project_hypermedia_links, generate_projects_collection_links
from validators.validators import validate_json

# Define the Blueprint
project_bp = Blueprint("project_routes", __name__, url_prefix="/projects")

@project_bp.route("/", methods=["POST"])
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
        cache_key = f"projects_{current_user_id}"
        cache.delete(cache_key)
        # Convert to dict and add hypermedia links
        project_dict = new_project.to_dict()
        project_dict = add_project_hypermedia_links(project_dict)
        return jsonify(project_dict), 201
    except ValueError as e:
        return handle_error(str(e), 400)
    except Exception as e:
        return handle_exception(e)

@project_bp.route("/<project_id>", methods=["GET"])
@jwt_required()
@cache.cached(
    timeout=300,
    key_prefix=lambda: f"project_{get_jwt_identity()}_{request.view_args['project_id']}",
)
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
        # Convert to dict and add hypermedia links
        project_dict = project.to_dict()
        project_dict = add_project_hypermedia_links(project_dict)
        return jsonify(project_dict), 200
    except Exception as e:
        return handle_exception(e)

@project_bp.route("/<project_id>", methods=["PUT"])
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
        cache_key = f"project_{current_user_id}_{project_id}"
        cache.delete(cache_key)
        # Also invalidate the all projects cache
        all_projects_cache_key = f"projects_{current_user_id}"
        cache.delete(all_projects_cache_key)
        # Convert to dict and add hypermedia links
        project_dict = updated_project.to_dict()
        project_dict = add_project_hypermedia_links(project_dict)
        return jsonify(project_dict), 200
    except ValueError as e:
        return handle_error(str(e), 400)
    except Exception as e:
        return handle_exception(e)

@project_bp.route("/<project_id>", methods=["DELETE"])
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
        # Invalidate related caches
        project_cache_key = f"project_{current_user_id}_{project_id}"
        cache.delete(project_cache_key)
        all_projects_cache_key = f"projects_{current_user_id}"
        cache.delete(all_projects_cache_key)
        # Generate navigation links after deletion
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
        # Structure the response with hypermedia
        if isinstance(projects, list):
            response = {
                "projects": [],
                "_links": generate_projects_collection_links()
            }
            for project in projects:
                if isinstance(project, dict):
                    response["projects"].append(add_project_hypermedia_links(project))
                else:
                    response["projects"].append(project)
        else:
            response = projects
        return jsonify(response), 200
    except Exception as e:
        return handle_exception(e)
