from flask import Blueprint, request, jsonify
from models import Task, Project, db, StatusEnum, PriorityEnum, get_all_tasks as get_tasks_model
from datetime import datetime
from uuid import UUID
import traceback
from schemas.schemas import TASK_SCHEMA, validate_schema
from auth import jwt_required  
from app import cache

# Create blueprint for task routes
task_bp = Blueprint('task_routes', __name__)

# Valid status and priority values
VALID_STATUS = [e.value for e in StatusEnum]
VALID_PRIORITY = [e.value for e in PriorityEnum]

@task_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad Request', 'message': str(error)}), 400

@task_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found', 'message': str(error)}), 404

@task_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal Server Error', 'message': str(error)}), 500

@task_bp.route('/tasks', methods=['POST'])
@jwt_required()
@cache.cached(timeout=60, query_string=True)
def create_task():
    try:
        data = request.get_json()
        error_response = validate_schema(data, TASK_SCHEMA)
        if error_response:
            return error_response
        if not data:
            return jsonify({'error': 'No input data provided'}), 400

        required_fields = ['project_id', 'title']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        try:
            project_id = UUID(data['project_id'])
            assignee_id = UUID(data['assignee_id']) if 'assignee_id' in data else None
        except ValueError as e:
            return jsonify({'error': f'Invalid UUID format: {str(e)}'}), 400

        deadline = None
        if 'deadline' in data:
            try:
                deadline = datetime.fromisoformat(data['deadline'].replace('Z', '+00:00'))
            except ValueError as e:
                return jsonify({'error': f'Invalid deadline format: {str(e)}. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400

        status = data.get('status', StatusEnum.PENDING.value)
        if status not in VALID_STATUS:
            return jsonify({'error': f'Invalid status. Must be one of: {", ".join(VALID_STATUS)}'}), 400

        priority = data.get('priority', PriorityEnum.LOW.value)
        if priority not in VALID_PRIORITY:
            return jsonify({'error': f'Invalid priority. Must be one of: {", ".join(map(str, VALID_PRIORITY))}'}), 400

        new_task = Task(
            title=data['title'],
            description=data.get('description'),
            priority=priority,
            deadline=deadline,
            status=status,
            project_id=project_id,
            assignee_id=assignee_id
        )
        
        db.session.add(new_task)
        db.session.commit()
        invalidate_task_cache()
        return jsonify(new_task.to_dict()), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@task_bp.route('/tasks', methods=['GET'])
@jwt_required()
@cache.cached(timeout=60, query_string=True)
def get_tasks():
    try:
        filters = {}
        assignee_id = request.args.get('assignee_id')
        project_id = request.args.get('project_id')
        status = request.args.get('status')

        if assignee_id:
            try:
                filters['assignee_id'] = UUID(assignee_id)
            except ValueError as e:
                return jsonify({'error': f'Invalid assignee_id format: {str(e)}'}), 400

        if project_id:
            try:
                filters['project_id'] = UUID(project_id)
            except ValueError as e:
                return jsonify({'error': f'Invalid project_id format: {str(e)}'}), 400

        if status:
            if status not in VALID_STATUS:
                return jsonify({'error': f'Invalid status. Must be one of: {", ".join(VALID_STATUS)}'}), 400
            filters['status'] = status

        tasks = get_tasks_model(**filters)
        return jsonify([task.to_dict() for task in tasks]), 200

    except Exception as e:
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@task_bp.route('/tasks/<task_id>', methods=['GET'])
@jwt_required()
@cache.cached(timeout=60, query_string=True)
def get_task(task_id):
    try:
        task = Task.query.get(UUID(task_id))
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        return jsonify(task.to_dict()), 200
    except ValueError as e:
        return jsonify({'error': f'Invalid task_id format: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@task_bp.route('/tasks/<task_id>', methods=['PUT'])
@jwt_required()
@cache.cached(timeout=60, query_string=True)
def update_task(task_id):
    try:
        task = Task.query.get(UUID(task_id))
        if not task:
            return jsonify({'error': 'Task not found'}), 404

        data = request.get_json()
        error_response = validate_schema(data, TASK_SCHEMA)
        if error_response:
            return error_response

        task.title = data.get('title', task.title)
        task.description = data.get('description', task.description)
        if 'priority' in data and data['priority'] in VALID_PRIORITY:
            task.priority = data['priority']
        if 'status' in data and data['status'] in VALID_STATUS:
            task.status = data['status']
        if 'deadline' in data:
            try:
                task.deadline = datetime.fromisoformat(data['deadline'].replace('Z', '+00:00'))
            except ValueError as e:
                return jsonify({'error': f'Invalid deadline format: {str(e)}'}), 400

        db.session.commit()
        invalidate_task_cache()
        return jsonify(task.to_dict()), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@task_bp.route('/tasks/<task_id>', methods=['DELETE'])
@jwt_required()
@cache.cached(timeout=60, query_string=True)
def delete_task(task_id):
    try:
        task = Task.query.get(UUID(task_id))
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        db.session.delete(task)
        db.session.commit()
        invalidate_task_cache()
        return '', 204
    except ValueError as e:
        return jsonify({'error': f'Invalid task_id format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


@task_bp.route('/projects', methods=['POST'])
@jwt_required()
@cache.cached(timeout=60, query_string=True)
def create_project():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400

        # Create new project
        new_project = Project(
            title=data['title'],
            description=data.get('description'),
            deadline=datetime.fromisoformat(data['deadline']) if 'deadline' in data else None,
            status=data.get('status', 'planning')
        )
        
        db.session.add(new_project)
        db.session.commit()
        invalidate_task_cache()
        return jsonify({
            'project_id': str(new_project.project_id),
            'title': new_project.title,
            'description': new_project.description,
            'status': new_project.status,
            'deadline': new_project.deadline.isoformat() if new_project.deadline else None
        }), 201

    except Exception as e:
        print(f"Exception in create_project: {str(e)}")
        print(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

def invalidate_task_cache():
    cache.delete_memoized(get_tasks)
    cache.delete_memoized(get_task)