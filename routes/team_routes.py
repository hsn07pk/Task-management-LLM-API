from flask import Blueprint, request, jsonify
from models import Team, User, TeamMembership, db
from uuid import UUID
import traceback

# Create blueprint for team routes
team_bp = Blueprint('team_routes', __name__)

@team_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad Request', 'message': str(error)}), 400

@team_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found', 'message': str(error)}), 404

@team_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal Server Error', 'message': str(error)}), 500

@team_bp.route('/teams', methods=['POST'])
def create_team_route():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400

        # Validate required fields
        required_fields = ['name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if lead_id is valid
        lead_id = None
        if 'lead_id' in data and data['lead_id']:
            try:
                lead_id = UUID(data['lead_id'])
                lead = User.query.get(lead_id)
                if not lead:
                    return jsonify({'error': 'Team lead user not found'}), 404
            except ValueError as e:
                return jsonify({'error': f'Invalid lead_id format: {str(e)}'}), 400

        # Create new team
        new_team = Team(
            name=data['name'],
            description=data.get('description'),
            lead_id=lead_id
        )
        
        db.session.add(new_team)
        db.session.commit()

        # Add the team lead as a member with 'leader' role if lead_id provided
        if lead_id:
            membership = TeamMembership(
                user_id=lead_id,
                team_id=new_team.team_id,
                role='leader'
            )
            db.session.add(membership)
            db.session.commit()

        return jsonify({
            'team_id': str(new_team.team_id),
            'name': new_team.name,
            'description': new_team.description,
            'lead_id': str(new_team.lead_id) if new_team.lead_id else None,
            'created_at': new_team.created_at.isoformat() if new_team.created_at else None
        }), 201

    except Exception as e:
        print(f"Exception in create_team: {str(e)}")
        print(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@team_bp.route('/teams', methods=['GET'])
def get_teams():
    try:
        teams = Team.query.all()
        result = []
        for team in teams:
            result.append({
                'team_id': str(team.team_id),
                'name': team.name,
                'description': team.description,
                'lead_id': str(team.lead_id) if team.lead_id else None,
                'created_at': team.created_at.isoformat() if team.created_at else None
            })
        return jsonify(result), 200

    except Exception as e:
        print(f"Exception in get_teams: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@team_bp.route('/teams/<team_id>', methods=['GET'])
def get_team(team_id):
    try:
        team_uuid = UUID(team_id)
        team = Team.query.get(team_uuid)
        
        if not team:
            return jsonify({'error': 'Team not found'}), 404

        # Get team members
        members = []
        memberships = TeamMembership.query.filter_by(team_id=team_uuid).all()
        for membership in memberships:
            user = User.query.get(membership.user_id)
            if user:
                members.append({
                    'user_id': str(user.user_id),
                    'username': user.username,
                    'role': membership.role
                })

        return jsonify({
            'team_id': str(team.team_id),
            'name': team.name,
            'description': team.description,
            'lead_id': str(team.lead_id) if team.lead_id else None,
            'created_at': team.created_at.isoformat() if team.created_at else None,
            'members': members
        }), 200

    except ValueError as e:
        return jsonify({'error': f'Invalid team_id format: {str(e)}'}), 400
    except Exception as e:
        print(f"Exception in get_team: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@team_bp.route('/teams/<team_id>', methods=['PUT'])
def update_team(team_id):
    try:
        team_uuid = UUID(team_id)
        team = Team.query.get(team_uuid)
        
        if not team:
            return jsonify({'error': 'Team not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400

        # Update fields if provided
        if 'name' in data:
            team.name = data['name']
            
        if 'description' in data:
            team.description = data['description']
            
        if 'lead_id' in data:
            if data['lead_id']:
                try:
                    lead_id = UUID(data['lead_id'])
                    lead = User.query.get(lead_id)
                    if not lead:
                        return jsonify({'error': 'Team lead user not found'}), 404
                    team.lead_id = lead_id
                    
                    # Update team membership to reflect new leader
                    existing_lead_membership = TeamMembership.query.filter_by(
                        team_id=team_uuid, 
                        user_id=lead_id
                    ).first()
                    
                    if existing_lead_membership:
                        existing_lead_membership.role = 'leader'
                    else:
                        new_lead_membership = TeamMembership(
                            user_id=lead_id,
                            team_id=team_uuid,
                            role='leader'
                        )
                        db.session.add(new_lead_membership)
                        
                except ValueError as e:
                    return jsonify({'error': f'Invalid lead_id format: {str(e)}'}), 400
            else:
                team.lead_id = None

        db.session.commit()
        return jsonify({
            'team_id': str(team.team_id),
            'name': team.name,
            'description': team.description,
            'lead_id': str(team.lead_id) if team.lead_id else None,
            'created_at': team.created_at.isoformat() if team.created_at else None
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Exception in update_team: {str(e)}")
        print(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@team_bp.route('/teams/<team_id>', methods=['DELETE'])
def delete_team(team_id):
    try:
        team_uuid = UUID(team_id)
        team = Team.query.get(team_uuid)
        
        if not team:
            return jsonify({'error': 'Team not found'}), 404

        db.session.delete(team)
        db.session.commit()
        
        return '', 204

    except ValueError as e:
        return jsonify({'error': f'Invalid team_id format: {str(e)}'}), 400
    except Exception as e:
        print(f"Exception in delete_team: {str(e)}")
        print(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

# Team Membership routes
@team_bp.route('/teams/<team_id>/members', methods=['POST'])
def add_team_member(team_id):
    try:
        team_uuid = UUID(team_id)
        team = Team.query.get(team_uuid)
        
        if not team:
            return jsonify({'error': 'Team not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400
            
        # Validate required fields
        if 'user_id' not in data:
            return jsonify({'error': 'Missing required field: user_id'}), 400
            
        try:
            user_id = UUID(data['user_id'])
            user = User.query.get(user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
        except ValueError as e:
            return jsonify({'error': f'Invalid user_id format: {str(e)}'}), 400
            
        # Check if user is already a member
        existing_membership = TeamMembership.query.filter_by(
            team_id=team_uuid, 
            user_id=user_id
        ).first()
        
        if existing_membership:
            return jsonify({'error': 'User is already a member of this team'}), 400
            
        # Add user to team
        role = data.get('role', 'member')
        
        # Validate role
        valid_roles = ['leader', 'member', 'admin']
        if role not in valid_roles:
            return jsonify({'error': f'Invalid role. Must be one of: {", ".join(valid_roles)}'}), 400
            
        membership = TeamMembership(
            user_id=user_id,
            team_id=team_uuid,
            role=role
        )
        
        db.session.add(membership)
        db.session.commit()
        
        return jsonify({
            'membership_id': str(membership.membership_id),
            'user_id': str(user_id),
            'team_id': str(team_uuid),
            'role': role
        }), 201

    except Exception as e:
        print(f"Exception in add_team_member: {str(e)}")
        print(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@team_bp.route('/teams/<team_id>/members/<user_id>', methods=['PUT'])
def update_team_member(team_id, user_id):
    try:
        team_uuid = UUID(team_id)
        user_uuid = UUID(user_id)
        
        # Check if team exists
        team = Team.query.get(team_uuid)
        if not team:
            return jsonify({'error': 'Team not found'}), 404
            
        # Check if user exists
        user = User.query.get(user_uuid)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Check if membership exists
        membership = TeamMembership.query.filter_by(
            team_id=team_uuid, 
            user_id=user_uuid
        ).first()
        
        if not membership:
            return jsonify({'error': 'User is not a member of this team'}), 404
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No input data provided'}), 400
            
        # Update role if provided
        if 'role' in data:
            role = data['role']
            valid_roles = ['leader', 'member', 'admin']
            if role not in valid_roles:
                return jsonify({'error': f'Invalid role. Must be one of: {", ".join(valid_roles)}'}), 400
                
            # If changing to leader, update the team's lead_id
            if role == 'leader':
                team.lead_id = user_uuid
                
            membership.role = role
            db.session.commit()
            
        return jsonify({
            'membership_id': str(membership.membership_id),
            'user_id': str(user_uuid),
            'team_id': str(team_uuid),
            'role': membership.role
        }), 200

    except ValueError as e:
        return jsonify({'error': f'Invalid UUID format: {str(e)}'}), 400
    except Exception as e:
        print(f"Exception in update_team_member: {str(e)}")
        print(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@team_bp.route('/teams/<team_id>/members/<user_id>', methods=['DELETE'])
def remove_team_member(team_id, user_id):
    try:
        team_uuid = UUID(team_id)
        user_uuid = UUID(user_id)
        
        # Check if membership exists
        membership = TeamMembership.query.filter_by(
            team_id=team_uuid, 
            user_id=user_uuid
        ).first()
        
        if not membership:
            return jsonify({'error': 'User is not a member of this team'}), 404
            
        # Check if user is the team lead, prevent deletion if true
        team = Team.query.get(team_uuid)
        if team.lead_id == user_uuid:
            return jsonify({'error': 'Cannot remove team leader. Assign a new leader first.'}), 400
            
        db.session.delete(membership)
        db.session.commit()
        
        return '', 204

    except ValueError as e:
        return jsonify({'error': f'Invalid UUID format: {str(e)}'}), 400
    except Exception as e:
        print(f"Exception in remove_team_member: {str(e)}")
        print(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500