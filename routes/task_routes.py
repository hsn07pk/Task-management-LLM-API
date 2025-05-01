from flask import Blueprint, jsonify, request, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from extentions.extensions import cache
from schemas.schemas import TASK_SCHEMA, TASK_UPDATE_SCHEMA
from services.task_service import TaskService
from utils.hypermedia.task_hypermedia import add_task_hypermedia_links, generate_tasks_collection_links
from validators.validators import validate_json

task_bp = Blueprint("task_routes", __name__, url_prefix="/tasks")

@task_bp.errorhandler(400)
def bad_request(error):
    response = {
        "error": "Bad Request", 
        "message": str(error),
        "_links": generate_tasks_collection_links()
    }
    return jsonify(response), 400

@task_bp.errorhandler(404)
def not_found(error):
    response = {
        "error": "Not Found", 
        "message": str(error),
        "_links": generate_tasks_collection_links()
    }
    return jsonify(response), 404

@task_bp.errorhandler(500)
def internal_error(error):
    response = {
        "error": "Internal Server Error", 
        "message": str(error),
        "_links": generate_tasks_collection_links()
    }
    return jsonify(response), 500

@task_bp.route("/", methods=["POST"])
@jwt_required()
@validate_json(TASK_SCHEMA)
def create_task():
    """
    Create a new task.
    """
    try:
        user_id = get_jwt_identity()
        if not user_id:
            response = {
                "error": "User not authenticated",
                "_links": generate_tasks_collection_links()
            }
            return jsonify(response), 401
        data = request.get_json()
        new_task = TaskService.create_task(data, user_id)
        
        # Ensure proper hypermedia links
        if isinstance(new_task, dict) and "task_id" in new_task:
            new_task = add_task_hypermedia_links(new_task)
            
            # Add location header for created resource
            response = jsonify(new_task)
            response.headers['Location'] = url_for('task_routes.task_operations', task_id=new_task['task_id'], _external=True)
            return response, 201
        else:
            response = {
                "error": "Task creation failed",
                "message": "Unable to create task with the provided data",
                "_links": generate_tasks_collection_links()
            }
            return jsonify(response), 500
    except ValueError as e:
        response = {
            "error": "Invalid data", 
            "message": str(e),
            "_links": generate_tasks_collection_links()
        }
        return jsonify(response), 400
    except Exception as e:
        response = {
            "error": "Internal server error", 
            "message": str(e),
            "_links": generate_tasks_collection_links()
        }
        return jsonify(response), 500

@task_bp.route("/<task_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def task_operations(task_id):
    """
    Operations for a single task: GET, PUT, DELETE.
    """
    try:
        user_id = get_jwt_identity()
        if not user_id:
            response = {
                "error": "User not authenticated",
                "_links": generate_tasks_collection_links()
            }
            return jsonify(response), 401

        if request.method == "GET":
            task = TaskService.get_task(task_id)
            if task is None:
                response = {
                    "error": "Not Found",
                    "message": f"Task with ID {task_id} not found",
                    "_links": generate_tasks_collection_links()
                }
                return jsonify(response), 404
                
            if isinstance(task, dict) and "id" in task:
                task = add_task_hypermedia_links(task)
            return jsonify(task), 200

        if request.method == "DELETE":
            # Check if task exists first
            task = TaskService.get_task(task_id)
            if task is None:
                response = {
                    "error": "Not Found",
                    "message": f"Task with ID {task_id} not found",
                    "_links": generate_tasks_collection_links()
                }
                return jsonify(response), 404
                
            TaskService.delete_task(task_id)
            
            # Clear cache if implemented
            task_cache_key = f"task_{user_id}_{task_id}"
            if hasattr(cache, 'delete'):
                cache.delete(task_cache_key)
                all_tasks_cache_key = f"tasks_{user_id}"
                cache.delete(all_tasks_cache_key)
                
            response = {
                "message": "Task deleted successfully",
                "_links": generate_tasks_collection_links()
            }
            return jsonify(response), 200

        if request.method == "PUT":
            # Check if task exists first
            task = TaskService.get_task(task_id)
            if task is None:
                response = {
                    "error": "Not Found",
                    "message": f"Task with ID {task_id} not found",
                    "_links": generate_tasks_collection_links()
                }
                return jsonify(response), 404
                
            data = request.get_json()
            if not data:
                response = {
                    "error": "No data provided",
                    "_links": generate_tasks_collection_links()
                }
                return jsonify(response), 400
                
            # Validate the data
            validate_json(TASK_UPDATE_SCHEMA)(lambda: None)()
            
            updated_task = TaskService.update_task(task_id, data, user_id)
            
            # Clear cache if implemented
            task_cache_key = f"task_{user_id}_{task_id}"
            if hasattr(cache, 'delete'):
                cache.delete(task_cache_key)
                all_tasks_cache_key = f"tasks_{user_id}"
                cache.delete(all_tasks_cache_key)
                
            if isinstance(updated_task, dict) and "id" in updated_task:
                updated_task = add_task_hypermedia_links(updated_task)
            return jsonify(updated_task), 200

    except ValueError as e:
        response = {
            "error": str(e),
            "_links": generate_tasks_collection_links()
        }
        return jsonify(response), 404
    except Exception as e:
        response = {
            "error": "Internal server error", 
            "message": str(e),
            "_links": generate_tasks_collection_links()
        }
        return jsonify(response), 500

@task_bp.route("/", methods=["GET"])
@jwt_required()
@cache.cached(timeout=300, key_prefix=lambda: f"tasks_{get_jwt_identity()}")
def get_tasks():
    """
    Get a list of tasks, possibly filtered.
    """
    try:
        user_id = get_jwt_identity()
        if not user_id:
            response = {
                "error": "User not authenticated",
                "_links": generate_tasks_collection_links()
            }
            return jsonify(response), 401

        filters = {
            "project_id": request.args.get("project_id"),
            "assignee_id": request.args.get("assignee_id"),
            "status": request.args.get("status"),
            "priority": request.args.get("priority"),
        }
        if filters["priority"] is not None:
            try:
                filters["priority"] = int(filters["priority"])
            except ValueError:
                response = {
                    "error": "Invalid priority value",
                    "_links": generate_tasks_collection_links()
                }
                return jsonify(response), 400
        filters = {k: v for k, v in filters.items() if v is not None}
        tasks = TaskService.get_tasks(filters)
        
        response = {
            "tasks": [],
            "_links": generate_tasks_collection_links(filters)
        }
        
        if isinstance(tasks, list):
            response["tasks"] = [add_task_hypermedia_links(task) for task in tasks if isinstance(task, dict) and "task_id" in task]
        else:
            # Handle edge case where tasks might not be a list
            response["error"] = "Unexpected response format"
            
        return jsonify(response), 200
    except ValueError as e:
        response = {
            "error": str(e),
            "_links": generate_tasks_collection_links()
        }
        return jsonify(response), 400
    except Exception as e:
        response = {
            "error": "Internal server error", 
            "message": str(e),
            "_links": generate_tasks_collection_links()
        }
        return jsonify(response), 500