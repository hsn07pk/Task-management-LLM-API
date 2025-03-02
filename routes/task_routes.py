from flask import Blueprint, request, jsonify
from models import Task, Project, Team, db, StatusEnum, PriorityEnum, get_all_tasks as get_tasks_model
from datetime import datetime
from uuid import UUID
import traceback

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
def create_task():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400

        # Validate required fields
        required_fields = ['project_id', 'title']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Parse and validate UUID fields
        try:
            project_id = UUID(data['project_id'])
            assignee_id = UUID(data['assignee_id']) if 'assignee_id' in data else None
        except ValueError as e:
            return jsonify({'error': f'Invalid UUID format: {str(e)}'}), 400

        # Parse deadline if provided
        deadline = None
        if 'deadline' in data:
            try:
                deadline = datetime.fromisoformat(data['deadline'].replace('Z', '+00:00'))
            except ValueError as e:
                return jsonify({'error': f'Invalid deadline format: {str(e)}. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400

        # Validate status
        status = data.get('status', StatusEnum.PENDING.value)
        if status not in VALID_STATUS:
            return jsonify({'error': f'Invalid status. Must be one of: {", ".join(VALID_STATUS)}'}), 400

        # Validate priority
        priority = data.get('priority', PriorityEnum.LOW.value)
        if priority not in VALID_PRIORITY:
            return jsonify({'error': f'Invalid priority. Must be one of: {", ".join(map(str, VALID_PRIORITY))}'}), 400

        # Create new task
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

        return jsonify(new_task.to_dict()), 201

    except ValueError as e:
        print(f"ValueError in create_task: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Exception in create_task: {str(e)}")
        print(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    try:
        assignee_id = request.args.get('assignee_id')
        project_id = request.args.get('project_id')
        status = request.args.get('status')

        filters = {}
        
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
        print(f"Exception in get_tasks: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@task_bp.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    try:
        task_uuid = UUID(task_id)
        task = Task.query.get(task_uuid)
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404

        return jsonify(task.to_dict()), 200

    except ValueError as e:
        return jsonify({'error': f'Invalid task_id format: {str(e)}'}), 400
    except Exception as e:
        print(f"Exception in get_task: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@task_bp.route('/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    try:
        task_uuid = UUID(task_id)
        task = Task.query.get(task_uuid)
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400

        # Update fields if provided
        if 'title' in data:
            task.title = data['title']
        if 'description' in data:
            task.description = data['description']
        if 'priority' in data:
            priority = data['priority']
            if priority not in VALID_PRIORITY:
                return jsonify({'error': f'Invalid priority. Must be one of: {", ".join(map(str, VALID_PRIORITY))}'}), 400
            task.priority = priority
        if 'status' in data:
            status = data['status']
            if status not in VALID_STATUS:
                return jsonify({'error': f'Invalid status. Must be one of: {", ".join(VALID_STATUS)}'}), 400
            task.status = status
        if 'deadline' in data:
            try:
                task.deadline = datetime.fromisoformat(data['deadline'].replace('Z', '+00:00'))
            except ValueError as e:
                return jsonify({'error': f'Invalid deadline format: {str(e)}. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400

        db.session.commit()
        return jsonify(task.to_dict()), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Exception in update_task: {str(e)}")
        print(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@task_bp.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:
        task_uuid = UUID(task_id)
        task = Task.query.get(task_uuid)
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404

        db.session.delete(task)
        db.session.commit()
        
        return '', 204

    except ValueError as e:
        return jsonify({'error': f'Invalid task_id format: {str(e)}'}), 400
    except Exception as e:
        print(f"Exception in delete_task: {str(e)}")
        print(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@task_bp.route('/projects', methods=['POST'])
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
