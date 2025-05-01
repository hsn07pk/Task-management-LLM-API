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

project_bp = Blueprint("project_routes", __name__, url_prefix="/projects")

@project_bp.errorhandler(400)
def bad_request(error):
    response = {
        "error": "Bad Request", 
        "message": str(error),
        "_links": generate_projects_collection_links()
    }
    return jsonify(response), 400

@project_bp.errorhandler(404)
def not_found(error):
    response = {
        "error": "Not Found", 
        "message": str(error),
        "_links": generate_projects_collection_links()
    }
    return jsonify(response), 404

@project_bp.errorhandler(500)
def internal_error(error):
    response = {
        "error": "Internal Server Error", 
        "message": str(error),
        "_links": generate_projects_collection_links()
    }
    return jsonify(response), 500

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
        response = {
            "error": "Invalid data", 
            "message": str(e),
            "_links": generate_projects_collection_links()
        }
        return jsonify(response), 400
    except Exception as e:
        response = {
            "error": "Internal server error", 
            "message": str(e),
            "_links": generate_projects_collection_links()
        }
        return jsonify(response), 500

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
        response = {
            "error": "Internal server error", 
            "message": str(e),
            "_links": generate_projects_collection_links()
        }
        return jsonify(response), 500

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
            response = {
                "error": "Not found", 
                "message": "Project not found",
                "_links": generate_projects_collection_links()
            }
            return jsonify(response), 404
        data = request.get_json()
        updated_project = ProjectService.update_project(project, data)

        # Invalidate caches
        cache.delete(f"project_{current_user_id}_{project_id}")
        cache.delete(f"projects_{current_user_id}")

        project_dict = add_project_hypermedia_links(updated_project.to_dict())
        cache_key = f"project_{current_user_id}_{project_id}"
        cache.delete(cache_key)
        all_projects_cache_key = f"projects_{current_user_id}"
        cache.delete(all_projects_cache_key)
        project_dict = updated_project.to_dict()
        project_dict = add_project_hypermedia_links(project_dict)
        return jsonify(project_dict), 200
    except ValueError as e:
        response = {
            "error": "Invalid data", 
            "message": str(e),
            "_links": generate_projects_collection_links()
        }
        return jsonify(response), 400
    except Exception as e:
        response = {
            "error": "Internal server error", 
            "message": str(e),
            "_links": generate_projects_collection_links()
        }
        return jsonify(response), 500

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
        project_cache_key = f"project_{current_user_id}_{project_id}"
        cache.delete(project_cache_key)
        all_projects_cache_key = f"projects_{current_user_id}"
        cache.delete(all_projects_cache_key)
        response = {
            "message": "Project deleted successfully",
            "_links": generate_projects_collection_links()
        }
        return jsonify(response), 200
    except Exception as e:
        response = {
            "error": "Internal server error", 
            "message": str(e),
            "_links": generate_projects_collection_links()
        }
        return jsonify(response), 500


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
