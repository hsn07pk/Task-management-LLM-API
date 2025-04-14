from flask import Blueprint, jsonify, request, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required

from extentions.extensions import cache
from models import User
from schemas.schemas import PROJECT_SCHEMA, PROJECT_UPDATE_SCHEMA
from services.project_services import ProjectService
from utils.error_handlers import handle_error, handle_exception
from validators.validators import validate_json

# Define the Blueprint
project_bp = Blueprint("project_routes", __name__, url_prefix="/projects")


def add_hypermedia_links(project_dict):
    """
    Add hypermedia links to a project resource.

    Args:
        project_dict (dict): The project dictionary to add links to

    Returns:
        dict: The project with added _links property
    """
    if not project_dict or not isinstance(project_dict, dict) or "id" not in project_dict:
        return project_dict

    # Create a deep copy of the project to avoid modifying the original
    project_with_links = dict(project_dict)

    # Convert project_id to string to ensure URL generation works correctly
    project_id = str(project_dict["id"])

    # Add links for the project resource
    project_with_links["_links"] = {
        "self": {
            "href": url_for("project_routes.get_project", project_id=project_id, _external=True)
        },
        "update": {
            "href": url_for("project_routes.update_project", project_id=project_id, _external=True)
        },
        "delete": {
            "href": url_for("project_routes.delete_project", project_id=project_id, _external=True)
        },
        "collection": {"href": url_for("project_routes.get_all_projects", _external=True)},
        "tasks": {"href": url_for("task_routes.get_tasks", project_id=project_id, _external=True)},
    }

    return project_with_links


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
        project_dict = add_hypermedia_links(project_dict)

        return jsonify(project_dict), 201

    except ValueError as e:
        return handle_error(str(e), 400)
    except Exception as e:
        return handle_exception(e)


@project_bp.route("/<uuid:project_id>", methods=["GET"])
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
        project_dict = add_hypermedia_links(project_dict)

        return jsonify(project_dict), 200

    except Exception as e:
        return handle_exception(e)


@project_bp.route("/<uuid:project_id>", methods=["PUT"])
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
        project_dict = add_hypermedia_links(project_dict)

        return jsonify(project_dict), 200

    except ValueError as e:
        return handle_error(str(e), 400)
    except Exception as e:
        return handle_exception(e)


@project_bp.route("/<uuid:project_id>", methods=["DELETE"])
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

        # Add navigation links after deletion
        response = {
            "message": "Project deleted successfully",
            "_links": {
                "projects": {"href": url_for("project_routes.get_all_projects", _external=True)},
                "create": {"href": url_for("project_routes.create_project", _external=True)},
            },
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
        print(current_user_id)
        current_user = User.query.get(current_user_id)
        if not current_user:
            return handle_error("Current user not found", 404)

        projects = ProjectService.fetch_all_projects()

        # Structure the response with hypermedia
        if isinstance(projects, list):
            # Format the response structure
            response = {
                "projects": [],
                "_links": {
                    "self": {"href": url_for("project_routes.get_all_projects", _external=True)},
                    "create": {"href": url_for("project_routes.create_project", _external=True)},
                },
            }

            # Add hypermedia links to each project
            for project in projects:
                if isinstance(project, dict):
                    response["projects"].append(add_hypermedia_links(project))
                else:
                    # Handle cases where items might not be dictionaries
                    response["projects"].append(project)
        else:
            # If not a list, maintain the original structure
            response = projects

        return jsonify(response), 200

    except Exception as e:
        return handle_exception(e)
