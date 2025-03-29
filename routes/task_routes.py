from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Task, Project, db, StatusEnum, PriorityEnum, User
from datetime import datetime
from uuid import UUID
import traceback
from validators.validators import validate_json
from schemas.schemas import TASK_SCHEMA
from extentions.extensions import cache  

# Create a new Blueprint for task-related routes
task_bp = Blueprint('task_routes', __name__)

# Define valid values for status and priority
VALID_STATUS = [e.value for e in StatusEnum]
VALID_PRIORITY_NAMES = [e.name for e in PriorityEnum]  # ['HIGH', 'MEDIUM', 'LOW']

# ---------------- ERROR HANDLERS ----------------

@task_bp.errorhandler(400)
def bad_request(error):
    """
    Handle 400 Bad Request errors.
    
    Args:
        error: The error object passed when a 400 error is encountered.
        
    Returns:
        A JSON response with an error message and a 400 status code.
    """
    return jsonify({'error': 'Bad Request', 'message': str(error)}), 400

@task_bp.errorhandler(404)
def not_found(error):
    """
    Handle 404 Not Found errors.
    
    Args:
        error: The error object passed when a 404 error is encountered.
        
    Returns:
        A JSON response with an error message and a 404 status code.
    """
    return jsonify({'error': 'Not Found', 'message': str(error)}), 404

@task_bp.errorhandler(500)
def internal_error(error):
    """
    Handle 500 Internal Server errors.
    
    Args:
        error: The error object passed when a 500 error is encountered.
        
    Returns:
        A JSON response with an error message and a 500 status code.
    """
    return jsonify({'error': 'Internal Server Error', 'message': str(error)}), 500

# ---------------- TASK ROUTES ----------------

@task_bp.route('/tasks', methods=['POST'])
@jwt_required()
@validate_json(TASK_SCHEMA)
def create_task():
    """
    Create a new task with validation and authentication.
    
    This route allows a user to create a new task, validating the provided data 
    (e.g., project_id, assignee_id, priority, etc.). The user must be authenticated 
    via JWT, and the input data must follow the TASK_SCHEMA.
    
    Returns:
        A JSON response with the created task's details and a 201 status code if successful, 
        or an error message with the appropriate HTTP status code if an issue arises.
    """
    try:
        # Get the authenticated user's ID from JWT
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
            
        data = request.get_json()
        
        # Validate user_id is a valid UUID
        try:
            created_by = UUID(user_id)
            updated_by = UUID(user_id)
        except ValueError:
            return jsonify({'error': 'Invalid user ID format'}), 400

        # Validate project_id is a valid UUID and exists
        try:
            if not data.get('project_id'):
                return jsonify({'error': 'Project ID is required'}), 400
                
            project_id = UUID(data['project_id'])
        except ValueError:
            return jsonify({'error': 'Invalid project_id format'}), 400
            
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Invalid project_id: Project not found'}), 404

        # Validate assignee_id if provided
        assignee_id = None
        if 'assignee_id' in data and data['assignee_id']:
            try:
                assignee_id = UUID(data['assignee_id'])
                assignee = User.query.get(assignee_id)
                if not assignee:
                    return jsonify({'error': 'Invalid assignee_id: User not found'}), 404
            except ValueError:
                return jsonify({'error': 'Invalid assignee_id format'}), 400

        # Parse deadline if provided
        deadline = None
        if 'deadline' in data and data['deadline']:
            try:
                deadline = datetime.fromisoformat(data['deadline'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid deadline format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400

        # Validate status and priority
        status = data.get('status', StatusEnum.PENDING.value)
        if status not in VALID_STATUS:
            return jsonify({'error': f'Invalid status value. Valid values are: {VALID_STATUS}'}), 400

        priority_str = data.get('priority', 'LOW').upper()
        try:
            priority = PriorityEnum[priority_str].value
        except KeyError:
            return jsonify({'error': f'Invalid priority value. Valid values are: {VALID_PRIORITY_NAMES}'}), 400

        # Create the task object and add it to the database
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
        return jsonify({'error': 'Invalid data format', 'message': str(e)}), 400
    except Exception as e:
        print(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


@task_bp.route('/tasks/<uuid:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    """
    Update an existing task.
    
    Args:
        task_id (uuid): The ID of the task to update.
    
    This route allows updating the details of a specific task, such as title, 
    description, priority, status, etc. The input data must include valid fields, 
    and only authenticated users can update the task.

    Returns:
        A JSON response with the updated task's details and a 200 status code if successful, 
        or an error message with the appropriate HTTP status code if an issue arises.
    """
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
            
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400

        # Update fields based on provided data
        if 'title' in data:
            task.title = data['title']
            
        if 'description' in data:
            task.description = data['description']
            
        if 'priority' in data:
            priority_str = data['priority'].upper()
            try:
                task.priority = PriorityEnum[priority_str].value
            except KeyError:
                return jsonify({'error': f'Invalid priority value. Valid values are: {VALID_PRIORITY_NAMES}'}), 400
                
        if 'status' in data:
            if data['status'] not in VALID_STATUS:
                return jsonify({'error': f'Invalid status value. Valid values are: {VALID_STATUS}'}), 400
            task.status = data['status']
            
        if 'deadline' in data:
            if data['deadline'] is None:
                task.deadline = None
            else:
                try:
                    task.deadline = datetime.fromisoformat(data['deadline'].replace('Z', '+00:00'))
                except ValueError:
                    return jsonify({'error': 'Invalid deadline format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400
                    
        if 'assignee_id' in data:
            if data['assignee_id'] is None:
                task.assignee_id = None
            else:
                try:
                    assignee_id = UUID(data['assignee_id'])
                    # Verify assignee exists
                    assignee = User.query.get(assignee_id)
                    if not assignee:
                        return jsonify({'error': 'Invalid assignee_id: User not found'}), 404
                    task.assignee_id = assignee_id
                except ValueError:
                    return jsonify({'error': 'Invalid assignee_id format'}), 400

        try:
            task.updated_by = UUID(user_id)
        except ValueError:
            return jsonify({'error': 'Invalid user ID format'}), 400
            
        db.session.commit()
        return jsonify(task.to_dict()), 200

    except Exception as e:
        print(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


@task_bp.route('/tasks/<uuid:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    """
    Delete a task by its ID.
    
    Args:
        task_id (uuid): The ID of the task to delete.
        
    Returns:
        A 204 status code if successful, or an error message with a 404 status code 
        if the task is not found.
    """
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
            
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
    """
    Retrieve all tasks with optional filters.
    
    This route allows users to get a list of tasks, with optional query parameters
    to filter tasks by project ID, assignee ID, or status.

    Query Parameters:
        - project_id: Filter tasks by project ID.
        - assignee_id: Filter tasks by assignee ID.
        - status: Filter tasks by status.

    Returns:
        A JSON response with a list of tasks matching the filters and a 200 status code,
        or an error message with an appropriate HTTP status code if an issue arises.
    """
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        project_id = request.args.get('project_id')
        assignee_id = request.args.get('assignee_id')
        status = request.args.get('status')

        # Build the query with optional filters
        query = Task.query
        
        if project_id:
            try:
                project_uuid = UUID(project_id)
                # Verify project exists
                project = Project.query.get(project_uuid)
                if not project:
                    return jsonify({'error': f'Project with ID {project_id} not found'}), 404
                query = query.filter_by(project_id=project_uuid)
            except ValueError:
                return jsonify({'error': 'Invalid project_id format'}), 400
                
        if assignee_id:
            try:
                assignee_uuid = UUID(assignee_id)
                # Verify assignee exists
                assignee = User.query.get(assignee_uuid)
                if not assignee:
                    return jsonify({'error': f'User with ID {assignee_id} not found'}), 404
                query = query.filter_by(assignee_id=assignee_uuid)
            except ValueError:
                return jsonify({'error': 'Invalid assignee_id format'}), 400
                
        if status:
            if status not in VALID_STATUS:
                return jsonify({'error': f'Invalid status value. Valid values are: {VALID_STATUS}'}), 400
            query = query.filter_by(status=status)

        tasks = query.all()
        return jsonify([task.to_dict() for task in tasks]), 200

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500