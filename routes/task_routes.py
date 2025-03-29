from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Task, Project, db, StatusEnum, PriorityEnum
from datetime import datetime
from uuid import UUID
import traceback
from validators.validators import validate_json
from schemas.schemas import TASK_SCHEMA
from extentions.extensions import cache  
from models import User
from models import StatusEnum, PriorityEnum 
task_bp = Blueprint('task_routes', __name__)

VALID_STATUS = [e.value for e in StatusEnum]
VALID_PRIORITY_NAMES = [e.name for e in PriorityEnum]  # ['HIGH', 'MEDIUM', 'LOW']

# ---------------- ERROR HANDLERS ----------------

@task_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad Request', 'message': str(error)}), 400

@task_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found', 'message': str(error)}), 404

@task_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal Server Error', 'message': str(error)}), 500

# ---------------- TASK ROUTES ----------------

@task_bp.route('/tasks', methods=['POST'])
@jwt_required()
@validate_json(TASK_SCHEMA)
def create_task():
    """Creates a new task with validation and authentication."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        created_by = UUID(user_id)
        updated_by = UUID(user_id)

        # Validate project_id exists
        project_id = UUID(data['project_id'])
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Invalid project_id: Project not found'}), 400

        # Validate assignee_id exists if provided
        assignee_id = None
        if 'assignee_id' in data:
            assignee_id = UUID(data['assignee_id'])
            assignee = User.query.get(assignee_id)
            if not assignee:
                return jsonify({'error': 'Invalid assignee_id: User not found'}), 400

        # Parse deadline if provided
        deadline = None
        if 'deadline' in data:
            deadline = datetime.fromisoformat(data['deadline'].replace('Z', '+00:00'))

        # Validate status and priority
        status = data.get('status', StatusEnum.PENDING.value)
        if status not in VALID_STATUS:
            return jsonify({'error': 'Invalid status value'}), 400

        priority_str = data.get('priority', 'LOW').upper()
        try:
            priority = PriorityEnum[priority_str].value
        except KeyError:
            return jsonify({'error': 'Invalid priority value'}), 400

        # Create the task
        new_task = Task(
            title=data['title'],
            description=data.get('description'),
            priority=priority,
            deadline=deadline,
            status=status,
            project_id=project_id,
            assignee_id=assignee_id,
            created_by=created_by,
            updated_by=updated_by
        )

        db.session.add(new_task)
        db.session.commit()
        return jsonify(new_task.to_dict()), 201

    except ValueError as e:
        return jsonify({'error': 'Invalid UUID format', 'message': str(e)}), 400
    except Exception as e:
        print(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


@task_bp.route('/tasks/<uuid:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    """Update an existing task."""
    try:
        user_id = get_jwt_identity()
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400

        if 'title' in data:
            task.title = data['title']
        if 'description' in data:
            task.description = data['description']
        if 'priority' in data:
            priority_str = data['priority'].upper()
            try:
                task.priority = PriorityEnum[priority_str].value
            except KeyError:
                return jsonify({'error': 'Invalid priority value'}), 400
        if 'status' in data:
            if data['status'] in VALID_STATUS:
                task.status = data['status']
            else:
                return jsonify({'error': 'Invalid status value'}), 400
        if 'deadline' in data:
            try:
                task.deadline = datetime.fromisoformat(data['deadline'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid deadline format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400
        if 'assignee_id' in data:
            try:
                task.assignee_id = UUID(data['assignee_id'])
            except ValueError:
                return jsonify({'error': 'Invalid assignee_id format'}), 400

        task.updated_by = user_id
        db.session.commit()
        return jsonify(task.to_dict()), 200

    except Exception as e:
        print(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500



@task_bp.route('/tasks/<uuid:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    """Delete a task."""
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404

        db.session.delete(task)
        db.session.commit()
        return '', 204

    except Exception as e:
        print(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500
    
@task_bp.route('/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    """Get all tasks with optional filters."""
    try:
        project_id = request.args.get('project_id')
        assignee_id = request.args.get('assignee_id')
        status = request.args.get('status')

        query = Task.query
        if project_id:
            query = query.filter_by(project_id=project_id)
        if assignee_id:
            query = query.filter_by(assignee_id=assignee_id)
        if status:
            query = query.filter_by(status=status)

        tasks = query.all()
        return jsonify([task.to_dict() for task in tasks]), 200

    except Exception as e:
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@task_bp.route('/tasks/<uuid:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    """Get a specific task by ID."""
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404

        return jsonify(task.to_dict()), 200

    except Exception as e:
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500