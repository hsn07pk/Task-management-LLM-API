# task_bp.py

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from services.task_service import TaskService
from schemas.schemas import TASK_SCHEMA
from validators.validators import validate_json

task_bp = Blueprint("task_routes", __name__)

@task_bp.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad Request", "message": str(error)}), 400

@task_bp.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found", "message": str(error)}), 404

@task_bp.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal Server Error", "message": str(error)}), 500

@task_bp.route("/tasks", methods=["POST"])
@jwt_required()
@validate_json(TASK_SCHEMA)
def create_task():
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        data = request.get_json()
        new_task = TaskService.create_task(data, user_id)
        return jsonify(new_task), 201
    except ValueError as e:
        return jsonify({"error": "Invalid data", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500

@task_bp.route("/tasks/<uuid:task_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def task_operations(task_id):
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        if request.method == "GET":
            task = TaskService.get_task(task_id)
            return jsonify(task), 200

        elif request.method == "DELETE":
            TaskService.delete_task(task_id)
            return jsonify({"message": "Task deleted successfully"}), 200

        elif request.method == "PUT":
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400

            updated_task = TaskService.update_task(task_id, data, user_id)
            return jsonify(updated_task), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500

@task_bp.route("/tasks", methods=["GET"])
@jwt_required()
def get_tasks():
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        filters = {
            "project_id": request.args.get("project_id"),
            "assignee_id": request.args.get("assignee_id"),
            "status": request.args.get("status")
        }
        filters = {k: v for k, v in filters.items() if v is not None}

        tasks = TaskService.get_tasks(filters)
        return jsonify(tasks), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
