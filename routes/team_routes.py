from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Team, TeamMembership, User
from uuid import UUID
from schemas.schemas import TEAM_SCHEMA, TEAM_MEMBERSHIP_SCHEMA
from validators.validators import validate_json
from extentions.extensions import cache
team_bp = Blueprint('team_routes', __name__)


# ------------------ ERROR HANDLERS ------------------

@team_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad Request', 'message': str(error)}), 400

@team_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found', 'message': str(error)}), 404

@team_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal Server Error', 'message': str(error)}), 500


# ------------------ TEAM ROUTES ------------------

# Create a new team
@team_bp.route('/teams', methods=['POST'])
@jwt_required()
@validate_json(TEAM_SCHEMA)
def create_team():
    """Creates a new team."""
    try:
        data = request.get_json()
        lead_id = UUID(data['lead_id'])

        new_team = Team(
            name=data['name'],
            description=data.get('description'),
            lead_id=lead_id
        )
        db.session.add(new_team)
        db.session.commit()

        return jsonify(new_team.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


# Get team details (with caching)
@team_bp.route('/teams/<uuid:team_id>', methods=['GET'])
@jwt_required()
@cache.cached(timeout=60)  # Cache this endpoint for 60 seconds
def get_team(team_id):
    """Retrieve team details."""
    team = Team.query.get(team_id)
    if not team:
        return jsonify({'error': 'Team not found'}), 404
    return jsonify(team.to_dict()), 200


# Update team details
@team_bp.route('/teams/<uuid:team_id>', methods=['PUT'])
@jwt_required()
@validate_json(TEAM_SCHEMA)
def update_team(team_id):
    """Update team details."""
    team = Team.query.get(team_id)
    if not team:
        return jsonify({'error': 'Team not found'}), 404

    data = request.get_json()
    if 'name' in data:
        team.name = data['name']
    if 'description' in data:
        team.description = data['description']
    if 'lead_id' in data:
        try:
            team.lead_id = UUID(data['lead_id'])
        except ValueError:
            return jsonify({'error': 'Invalid lead_id format'}), 400

    db.session.commit()
    return jsonify(team.to_dict()), 200


# Delete a team
@team_bp.route('/teams/<uuid:team_id>', methods=['DELETE'])
@jwt_required()
def delete_team(team_id):
    """Delete a team."""
    team = Team.query.get(team_id)
    if not team:
        return jsonify({'error': 'Team not found'}), 404

    db.session.delete(team)
    db.session.commit()
    return jsonify({'message': 'Team deleted successfully'}), 200


# ------------------ TEAM MEMBERSHIP ROUTES ------------------

# Add a member to a team
@team_bp.route('/teams/<uuid:team_id>/members', methods=['POST'])
@jwt_required()
@validate_json(TEAM_MEMBERSHIP_SCHEMA)
def add_team_member(team_id):
    """Adds a user to a team with a specified role."""
    try:
        data = request.get_json()
        user_id = UUID(data['user_id'])

        # Check if the user already exists in the team
        existing_member = TeamMembership.query.filter_by(team_id=team_id, user_id=user_id).first()
        if existing_member:
            return jsonify({'error': 'User is already a member of this team'}), 400

        membership = TeamMembership(
            user_id=user_id,
            team_id=team_id,
            role=data['role']
        )
        db.session.add(membership)
        db.session.commit()
        return jsonify({'message': 'Member added successfully'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


# Update a member's role in the team
@team_bp.route('/teams/<uuid:team_id>/members/<uuid:user_id>', methods=['PUT'])
@jwt_required()
@validate_json({'type': 'object', 'properties': {'role': {'type': 'string'}}, 'required': ['role']})
def update_team_member(team_id, user_id):
    """Updates a team member's role."""
    membership = TeamMembership.query.filter_by(team_id=team_id, user_id=user_id).first()
    if not membership:
        return jsonify({'error': 'Membership not found'}), 404

    data = request.get_json()
    membership.role = data['role']
    db.session.commit()
    return jsonify({'message': 'Member role updated successfully'}), 200


# Remove a member from the team
@team_bp.route('/teams/<uuid:team_id>/members/<uuid:user_id>', methods=['DELETE'])
@jwt_required()
def remove_team_member(team_id, user_id):
    """Removes a user from a team."""
    membership = TeamMembership.query.filter_by(team_id=team_id, user_id=user_id).first()
    if not membership:
        return jsonify({'error': 'Membership not found'}), 404

    db.session.delete(membership)
    db.session.commit()
    return jsonify({'message': 'Member removed successfully'}), 200


# Get all members of a team (with caching)
@team_bp.route('/teams/<uuid:team_id>/members', methods=['GET'])
@jwt_required()
@cache.cached(timeout=60)  # Cache this endpoint for 60 seconds
def get_team_members(team_id):
    """Retrieve all members of a team."""
    team = Team.query.get(team_id)
    if not team:
        return jsonify({'error': 'Team not found'}), 404

    members = TeamMembership.query.filter_by(team_id=team_id).all()
    member_list = [
        {
            'user_id': str(member.user_id),
            'role': member.role,
            '_links': {'self': f'/users/{member.user_id}'}
        }
        for member in members
    ]
    return jsonify({'team_id': str(team_id), 'members': member_list}), 200
