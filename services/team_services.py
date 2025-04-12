import traceback
from uuid import UUID

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extentions.extensions import cache
from models import Team, TeamMembership, User, db
from schemas.schemas import TEAM_MEMBERSHIP_SCHEMA, TEAM_SCHEMA
from validators.validators import validate_json

# Blueprint for team-related routes
team_bp = Blueprint("team_routes", __name__)

# ------------------ ERROR HANDLERS ------------------


@team_bp.errorhandler(400)
def bad_request(error):
    """Handles 400 errors (Bad Request)."""
    return jsonify({"error": "Bad Request", "message": str(error)}), 400


@team_bp.errorhandler(404)
def not_found(error):
    """Handles 404 errors (Not Found)."""
    return jsonify({"error": "Not Found", "message": str(error)}), 404


@team_bp.errorhandler(500)
def internal_error(error):
    """Handles 500 errors (Internal Server Error)."""
    return jsonify({"error": "Internal Server Error", "message": str(error)}), 500


# ------------------ TEAM SERVICE CLASS ------------------
class TeamService:
    """
    Service class to encapsulate team operations.
    """
    
    @staticmethod
    def create_team(user_id, data):
        """
        Creates a new team.
        
        :param user_id: UUID of the authenticated user
        :param data: Team data dictionary
        :return: Tuple of (team_dict, status_code) or (error_dict, status_code)
        """
        try:
            if not user_id:
                return {"error": "User not authenticated"}, 401

            # Validate lead_id is a valid UUID and exists
            try:
                if not data.get("lead_id"):
                    return {"error": "Lead ID is required"}, 400

                lead_id = UUID(data["lead_id"])
            except ValueError:
                return {"error": "Invalid lead_id format"}, 400

            # Check if lead exists
            lead = User.query.get(lead_id)
            if not lead:
                return {"error": "Invalid lead_id: User not found"}, 404

            # Create a new team object
            new_team = Team(name=data["name"], description=data.get("description"), lead_id=lead_id)

            # Add the team to the session and commit to the database
            db.session.add(new_team)
            db.session.commit()

            return new_team.to_dict(), 201

        except Exception as e:
            db.session.rollback()
            print(traceback.format_exc())
            return {"error": "Internal server error", "message": str(e)}, 500
    
    @staticmethod
    def get_team(user_id, team_id):
        """
        Retrieves details of a specific team.
        
        :param user_id: UUID of the authenticated user
        :param team_id: UUID of the team to retrieve
        :return: Tuple of (team_dict, status_code) or (error_dict, status_code)
        """
        try:
            if not user_id:
                return {"error": "User not authenticated"}, 401

            team = Team.query.get(team_id)
            if not team:
                return {"error": "Team not found"}, 404
            return team.to_dict(), 200

        except Exception as e:
            print(traceback.format_exc())
            return {"error": "Internal server error", "message": str(e)}, 500
    
    @staticmethod
    def update_team(user_id, team_id, data):
        """
        Updates an existing team's details.
        
        :param user_id: UUID of the authenticated user
        :param team_id: UUID of the team to update
        :param data: Dictionary with updated team data
        :return: Tuple of (team_dict, status_code) or (error_dict, status_code)
        """
        try:
            if not user_id:
                return {"error": "User not authenticated"}, 401

            team = Team.query.get(team_id)
            if not team:
                return {"error": "Team not found"}, 404

            if not data:
                return {"error": "No input data provided"}, 400

            if "name" in data:
                team.name = data["name"]

            if "description" in data:
                team.description = data["description"]

            if "lead_id" in data:
                try:
                    lead_id = UUID(data["lead_id"])
                    # Verify lead exists
                    lead = User.query.get(lead_id)
                    if not lead:
                        return {"error": "Invalid lead_id: User not found"}, 404
                    team.lead_id = lead_id
                except ValueError:
                    return {"error": "Invalid lead_id format"}, 400

            db.session.commit()
            return team.to_dict(), 200

        except Exception as e:
            db.session.rollback()
            print(traceback.format_exc())
            return {"error": "Internal server error", "message": str(e)}, 500
    
    @staticmethod
    def delete_team(user_id, team_id):
        """
        Deletes a team.
        
        :param user_id: UUID of the authenticated user
        :param team_id: UUID of the team to delete
        :return: Tuple of (message_dict, status_code) or (error_dict, status_code)
        """
        try:
            if not user_id:
                return {"error": "User not authenticated"}, 401

            team = Team.query.get(team_id)
            if not team:
                return {"error": "Team not found"}, 404

            db.session.delete(team)
            db.session.commit()
            return {"message": "Team deleted successfully"}, 200

        except Exception as e:
            db.session.rollback()
            print(traceback.format_exc())
            return {"error": "Internal server error", "message": str(e)}, 500
    
    @staticmethod
    def add_team_member(current_user_id, team_id, data):
        """
        Adds a user to a team with a specified role.
        
        :param current_user_id: UUID of the authenticated user
        :param team_id: UUID of the team
        :param data: Dictionary with user_id and role
        :return: Tuple of (message_dict, status_code) or (error_dict, status_code)
        """
        try:
            if not current_user_id:
                return {"error": "User not authenticated"}, 401

            # Check if team exists
            team = Team.query.get(team_id)
            if not team:
                return {"error": "Team not found"}, 404

            if not data:
                return {"error": "No input data provided"}, 400

            if "user_id" not in data or not data["user_id"]:
                return {"error": "User ID is required"}, 400

            if "role" not in data or not data["role"]:
                return {"error": "Role is required"}, 400

            try:
                user_id = UUID(data["user_id"])
            except ValueError:
                return {"error": "Invalid user_id format"}, 400

            # Verify user exists
            user = User.query.get(user_id)
            if not user:
                return {"error": "User not found"}, 404

            # Check if the user is already a member of the team
            existing_member = TeamMembership.query.filter_by(team_id=team_id, user_id=user_id).first()
            if existing_member:
                return {"error": "User is already a member of this team"}, 400

            membership = TeamMembership(user_id=user_id, team_id=team_id, role=data["role"])
            db.session.add(membership)
            db.session.commit()
            return {"message": "Member added successfully"}, 201

        except Exception as e:
            db.session.rollback()
            print(traceback.format_exc())
            return {"error": "Internal server error", "message": str(e)}, 500
    
    @staticmethod
    def update_team_member(current_user_id, team_id, user_id, data):
        """
        Updates the role of a member in a team.
        
        :param current_user_id: UUID of the authenticated user
        :param team_id: UUID of the team
        :param user_id: UUID of the user whose role will be updated
        :param data: Dictionary with new role
        :return: Tuple of (message_dict, status_code) or (error_dict, status_code)
        """
        try:
            if not current_user_id:
                return {"error": "User not authenticated"}, 401

            # Check if team exists
            team = Team.query.get(team_id)
            if not team:
                return {"error": "Team not found"}, 404

            # Check if user exists
            user = User.query.get(user_id)
            if not user:
                return {"error": "User not found"}, 404

            membership = TeamMembership.query.filter_by(team_id=team_id, user_id=user_id).first()
            if not membership:
                return {"error": "Membership not found"}, 404

            if not data:
                return {"error": "No input data provided"}, 400

            if "role" not in data or not data["role"]:
                return {"error": "Role is required"}, 400

            membership.role = data["role"]
            db.session.commit()
            return {"message": "Member role updated successfully"}, 200

        except Exception as e:
            db.session.rollback()
            print(traceback.format_exc())
            return {"error": "Internal server error", "message": str(e)}, 500
    
    @staticmethod
    def remove_team_member(current_user_id, team_id, user_id):
        """
        Removes a user from a team.
        
        :param current_user_id: UUID of the authenticated user
        :param team_id: UUID of the team
        :param user_id: UUID of the user to be removed
        :return: Tuple of (message_dict, status_code) or (error_dict, status_code)
        """
        try:
            if not current_user_id:
                return {"error": "User not authenticated"}, 401

            # Check if team exists
            team = Team.query.get(team_id)
            if not team:
                return {"error": "Team not found"}, 404

            # Check if user exists
            user = User.query.get(user_id)
            if not user:
                return {"error": "User not found"}, 404

            membership = TeamMembership.query.filter_by(team_id=team_id, user_id=user_id).first()
            if not membership:
                return {"error": "Membership not found"}, 404

            db.session.delete(membership)
            db.session.commit()
            return {"message": "Member removed successfully"}, 200

        except Exception as e:
            db.session.rollback()
            print(traceback.format_exc())
            return {"error": "Internal server error", "message": str(e)}, 500
    
    @staticmethod
    def get_team_members(current_user_id, team_id):
        """
        Retrieves all members of a specific team.
        
        :param current_user_id: UUID of the authenticated user
        :param team_id: UUID of the team
        :return: Tuple of (members_dict, status_code) or (error_dict, status_code)
        """
        try:
            if not current_user_id:
                return {"error": "User not authenticated"}, 401

            team = Team.query.get(team_id)
            if not team:
                return {"error": "Team not found"}, 404

            members = TeamMembership.query.filter_by(team_id=team_id).all()
            member_list = [
                {
                    "user_id": str(member.user_id),
                    "role": member.role,
                    "_links": {"self": f"/users/{member.user_id}"},
                }
                for member in members
            ]
            return {"team_id": str(team_id), "members": member_list}, 200

        except Exception as e:
            print(traceback.format_exc())
            return {"error": "Internal server error", "message": str(e)}, 500

