from flask import Blueprint, jsonify, request, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from extentions.extensions import cache
from schemas.schemas import TASK_SCHEMA
from services.task_service import TaskService
from utils.hypermedia.task_hypermedia import add_task_hypermedia_links, generate_tasks_collection_links
from validators.validators import validate_json

task_bp = Blueprint("task_routes", __name__, url_prefix="/tasks")

@task_bp.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad Request", "message": str(error)}), 400

@task_bp.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found", "message": str(error)}), 404

@task_bp.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal Server Error", "message": str(error)}), 500

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
            return jsonify({"error": "User not authenticated"}), 401
        data = request.get_json()
        new_task = TaskService.create_task(data, user_id)
        if isinstance(new_task, dict) and "id" in new_task:
            new_task = add_task_hypermedia_links(new_task)
        return jsonify(new_task), 201
    except ValueError as e:
        return jsonify({"error": "Invalid data", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500

@task_bp.route("/<task_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def task_operations(task_id):
    """
    Operations for a single task: GET, PUT, DELETE.
    """
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        if request.method == "GET":
            task = TaskService.get_task(task_id)
            if isinstance(task, dict) and "id" in task:
                task = add_task_hypermedia_links(task)
            return jsonify(task), 200

        if request.method == "DELETE":
            TaskService.delete_task(task_id)
            response = {
                "message": "Task deleted successfully",
                "_links": generate_tasks_collection_links()
            }
            return jsonify(response), 200

        if request.method == "PUT":
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400
            updated_task = TaskService.update_task(task_id, data, user_id)
            if isinstance(updated_task, dict) and "id" in updated_task:
                updated_task = add_task_hypermedia_links(updated_task)
            return jsonify(updated_task), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500

@task_bp.route("/", methods=["GET"])
@jwt_required()
def get_tasks():
    """
    Get a list of tasks, possibly filtered.
    """
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

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
                return jsonify({"error": "Invalid priority value"}), 400
        filters = {k: v for k, v in filters.items() if v is not None}
        tasks = TaskService.get_tasks(filters)
        
        response = {
            "tasks": [],
            "_links": generate_tasks_collection_links(filters)
        }
        
        if isinstance(tasks, list):
            response["tasks"] = [add_task_hypermedia_links(task) for task in tasks if isinstance(task, dict) and "id" in task]
        else:
            # Handle edge case where tasks might not be a list
            response["error"] = "Unexpected response format"
            
        return jsonify(response), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500