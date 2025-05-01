from flask import Blueprint, jsonify, request, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from extentions.extensions import cache
from models import User
from schemas.schemas import PROJECT_SCHEMA, PROJECT_UPDATE_SCHEMA
from services.project_services import ProjectService
from utils.error_handlers import handle_error, handle_exception
from utils.hypermedia.project_hypermedia import add_project_hypermedia_links, generate_projects_collection_links
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
    """Creates a new project."""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if not current_user:
            response = {
                "error": "User not found", 
                "message": "Current user not found",
                "_links": generate_projects_collection_links()
            }
            return jsonify(response), 404
        data = request.get_json()
        new_project = ProjectService.create_project(data)
        cache_key = f"projects_{current_user_id}"
        cache.delete(cache_key)
        project_dict = new_project.to_dict()
        project_dict = add_project_hypermedia_links(project_dict)
        
        # Add location header for created resource
        response = jsonify(project_dict)
        response.headers['Location'] = url_for('project_routes.get_project', project_id=project_dict['team_id'], _external=True)
        return response, 201
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
            response = {
                "error": "User not found", 
                "message": "Current user not found",
                "_links": generate_projects_collection_links()
            }
            return jsonify(response), 404
        project = ProjectService.get_project(project_id)
        if not project:
            response = {
                "error": "Not found", 
                "message": "Project not found",
                "_links": generate_projects_collection_links()
            }
            return jsonify(response), 404
        project_dict = project.to_dict()
        project_dict = add_project_hypermedia_links(project_dict)
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
    """Updates an existing project."""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if not current_user:
            response = {
                "error": "User not found", 
                "message": "Current user not found",
                "_links": generate_projects_collection_links()
            }
            return jsonify(response), 404
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
    """Deletes a project."""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        if not current_user:
            response = {
                "error": "User not found", 
                "message": "Current user not found",
                "_links": generate_projects_collection_links()
            }
            return jsonify(response), 404
        project = ProjectService.get_project(project_id)
        if not project:
            response = {
                "error": "Not found", 
                "message": "Project not found",
                "_links": generate_projects_collection_links()
            }
            return jsonify(response), 404
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
            response = {
                "error": "User not found", 
                "message": "Current user not found",
                "_links": generate_projects_collection_links()
            }
            return jsonify(response), 404
            
        # Get any filter parameters
        filters = {
            "status": request.args.get("status"),
            "priority": request.args.get("priority"),
        }
        filters = {k: v for k, v in filters.items() if v is not None}
            
        projects = ProjectService.fetch_all_projects()
        
        response = {
            "projects": [],
            "_links": generate_projects_collection_links(filters)
        }
        
        if isinstance(projects, list):
            for project in projects:
                if isinstance(project, dict) and "id" in project:
                    response["projects"].append(add_project_hypermedia_links(project))
                else:
                    response["projects"].append(project)
        else:
            # Handle edge case where projects might not be a list
            response["error"] = "Unexpected response format"
            
        return jsonify(response), 200
    except Exception as e:
        response = {
            "error": "Internal server error", 
            "message": str(e),
            "_links": generate_projects_collection_links()
        }
        return jsonify(response), 500