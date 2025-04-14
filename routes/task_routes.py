from flask import Blueprint, jsonify, request, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required

from extentions.extensions import cache
from schemas.schemas import TASK_SCHEMA
from services.task_service import TaskService
from validators.validators import validate_json

task_bp = Blueprint("task_routes", __name__, url_prefix="/tasks")


def add_hypermedia_links(task):
    """
    Add hypermedia links to a task resource.

    Args:
        task (dict): The task dictionary to add links to

    Returns:
        dict: The task with added _links property
    """
    if not task or not isinstance(task, dict) or "id" not in task:
        return task

    # Create a deep copy of the task to avoid modifying the original
    task_with_links = dict(task)

    # Convert task_id to string to ensure URL generation works correctly
    task_id = str(task["id"])

    # Add links for the task resource
    task_with_links["_links"] = {
        "self": {"href": url_for("task_routes.task_operations", task_id=task_id, _external=True)},
        "collection": {"href": url_for("task_routes.get_tasks", _external=True)},
    }

    # We'll avoid making assumptions about other routes that might not exist
    # Instead, we'll only include links we're sure about

    return task_with_links


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
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        data = request.get_json()
        new_task = TaskService.create_task(data, user_id)

        # Add hypermedia links to the newly created task
        if isinstance(new_task, dict) and "id" in new_task:
            new_task = add_hypermedia_links(new_task)

        return jsonify(new_task), 201
    except ValueError as e:
        return jsonify({"error": "Invalid data", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


@task_bp.route("/<uuid:task_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def task_operations(task_id):
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        if request.method == "GET":
            task = TaskService.get_task(task_id)

            # Add hypermedia links to the retrieved task
            if isinstance(task, dict) and "id" in task:
                task = add_hypermedia_links(task)

            return jsonify(task), 200

        if request.method == "DELETE":
            TaskService.delete_task(task_id)

            # Add hypermedia links for navigation after deletion
            response = {
                "message": "Task deleted successfully",
                "_links": {"tasks": {"href": url_for("task_routes.get_tasks", _external=True)}},
            }

            return jsonify(response), 200

        if request.method == "PUT":
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400

            updated_task = TaskService.update_task(task_id, data, user_id)

            # Add hypermedia links to the updated task
            if isinstance(updated_task, dict) and "id" in updated_task:
                updated_task = add_hypermedia_links(updated_task)

            return jsonify(updated_task), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


@task_bp.route("/", methods=["GET"])
@jwt_required()
def get_tasks():
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        filters = {
            "project_id": request.args.get("project_id"),
            "assignee_id": request.args.get("assignee_id"),
            "status": request.args.get("status"),
        }
        filters = {k: v for k, v in filters.items() if v is not None}

        tasks = TaskService.get_tasks(filters)

        # Prepare response structure with hypermedia links
        if not isinstance(tasks, list):
            # If it's not a list, keep the original structure
            response = tasks
        else:
            # If it's a list, wrap it with additional metadata
            response = {
                "tasks": [add_hypermedia_links(task) for task in tasks],
                "_links": {
                    "self": {
                        "href": url_for(
                            "task_routes.get_tasks",
                            **{k: v for k, v in request.args.items()},
                            _external=True,
                        )
                    },
                    "create": {"href": url_for("task_routes.create_task", _external=True)},
                },
            }

        return jsonify(response), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
