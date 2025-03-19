from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Project, Team, db
from uuid import UUID
import traceback
from validators.validators import validate_json
from schemas.schemas import PROJECT_SCHEMA
from extentions.extensions import cache

project_bp = Blueprint('project_routes', __name__)


# ------------------ ERROR HANDLERS ------------------
@project_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad Request', 'message': str(error)}), 400

@project_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found', 'message': str(error)}), 404

@project_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal Server Error', 'message': str(error)}), 500

# ------------------ PROJECT ROUTES ------------------
@project_bp.route('/projects', methods=['POST'])
@jwt_required()
@validate_json(PROJECT_SCHEMA)
def create_project():
    """Create a new project."""
    try:
        data = request.get_json()
        team_id = UUID(data['team_id'])
        
        # Validate team exists
        team = Team.query.get(team_id)
        if not team:
            return jsonify({'error': 'Team not found'}), 404

        new_project = Project(
            title=data['title'],
            description=data.get('description'),
            team_id=team_id,
            category_id=UUID(data['category_id']) if 'category_id' in data else None
        )
        
        db.session.add(new_project)
        db.session.commit()
        return jsonify(new_project.to_dict()), 201

    except ValueError as e:
        return jsonify({'error': 'Invalid UUID format', 'message': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@project_bp.route('/projects/<uuid:project_id>', methods=['GET'])
@jwt_required()
@cache.cached(timeout=60)
def get_project(project_id):
    """Get project details."""
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    return jsonify(project.to_dict()), 200

@project_bp.route('/projects/<uuid:project_id>', methods=['PUT'])
@jwt_required()
@validate_json(PROJECT_SCHEMA)
def update_project(project_id):
    """Update project details."""
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    data = request.get_json()
    if 'title' in data:
        project.title = data['title']
    if 'description' in data:
        project.description = data['description']
    if 'team_id' in data:
        project.team_id = UUID(data['team_id'])
    if 'category_id' in data:
        project.category_id = UUID(data['category_id']) if data['category_id'] else None

    db.session.commit()
    return jsonify(project.to_dict()), 200

@project_bp.route('/projects/<uuid:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    """Delete a project."""
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    db.session.delete(project)
    db.session.commit()
    return jsonify({'message': 'Project deleted successfully'}), 200