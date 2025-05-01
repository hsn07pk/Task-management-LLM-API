from flask import Blueprint, jsonify, request, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from extentions.extensions import cache
from schemas.schemas import TEAM_MEMBERSHIP_SCHEMA, TEAM_SCHEMA, TEAM_UPDATE_SCHEMA
from services.team_services import TeamService
from utils.hypermedia.link_builder import build_standard_links
from validators.validators import validate_json

team_bp = Blueprint("team_routes", __name__, url_prefix="/teams")

def generate_team_hypermedia_links(team_id=None, members=False):
    """
    Generate hypermedia links for team resources.
    
    Args:
        team_id (str, optional): The ID of the specific team
        members (bool): Whether to include links to team member resources
        
    Returns:
        dict: A dictionary of links
    """
    links = build_standard_links("team", team_id)
    
    # Add team-specific links
    if team_id:
        team_specific = {
            "update": {
                "href": url_for("team_routes.update_team", team_id=team_id, _external=True),
                "method": "PUT",
                "schema": "/schemas/team-update.json"
            },
            "delete": {
                "href": url_for("team_routes.delete_team", team_id=team_id, _external=True),
                "method": "DELETE"
            },
            "members": {
                "href": url_for("team_routes.get_team_members", team_id=team_id, _external=True),
                "method": "GET"
            }
        }
        links.update(team_specific)
        
        # If this is a members response, add member-specific links
        if members:
            member_links = {
                "add_member": {
                    "href": url_for("team_routes.add_team_member", team_id=team_id, _external=True),
                    "method": "POST",
                    "schema": "/schemas/team-membership.json"
                }
            }
            links.update(member_links)
    else:
        # Collection-specific links
        collection_links = {
            "create": {
                "href": url_for("team_routes.create_team", _external=True),
                "method": "POST",
                "schema": "/schemas/team.json"
            }
        }
        links.update(collection_links)
    
    return links


def generate_team_member_links(team_id, user_id=None):
    """
    Generate hypermedia links for team member resources.
    
    Args:
        team_id (str): The team ID
        user_id (str, optional): The user ID of the team member
        
    Returns:
        dict: A dictionary of links
    """
    links = {
        "team": {
            "href": url_for("team_routes.get_team", team_id=team_id, _external=True),
            "method": "GET"
        },
        "members": {
            "href": url_for("team_routes.get_team_members", team_id=team_id, _external=True),
            "method": "GET"
        },
        "root": {
            "href": url_for("entry_point.api_root", _external=True),
            "method": "GET"
        }
    }
    
    # Add member-specific links if user_id is provided
    if user_id:
        member_specific = {
            "update": {
                "href": url_for(
                    "team_routes.update_team_member", 
                    team_id=team_id, 
                    user_id=user_id, 
                    _external=True
                ),
                "method": "PUT",
                "schema": "/schemas/team-membership-update.json"
            },
            "delete": {
                "href": url_for(
                    "team_routes.remove_team_member", 
                    team_id=team_id, 
                    user_id=user_id, 
                    _external=True
                ),
                "method": "DELETE"
            },
            "user": {
                "href": url_for("user_routes.get_user", user_id=user_id, _external=True),
                "method": "GET"
            }
        }
        links.update(member_specific)
    else:
        # Collection-specific links
        collection_links = {
            "add_member": {
                "href": url_for("team_routes.add_team_member", team_id=team_id, _external=True),
                "method": "POST",
                "schema": "/schemas/team-membership.json"
            }
        }
        links.update(collection_links)
    
    return links


@team_bp.route("/", methods=["GET"])
@jwt_required()
@cache.cached(timeout=200, key_prefix=lambda: f"team_all_{get_jwt_identity()}")
def get_all_teams():
    """
    Retrieves all teams the authenticated user is a member of.

    Returns:
        - List of teams with their basic info and the user's role.
        - HTTP Status Code: 200 (OK) on success.
    """
    result, status_code = TeamService.get_all_teams()
    response = {
        "teams": [],
        "_links": generate_team_hypermedia_links()
    }
    if status_code == 200 and isinstance(result, list):
        for team in result:
            if isinstance(team, dict) and "id" in team:
                team_with_links = dict(team)
                team_with_links["_links"] = generate_team_hypermedia_links(team_id=str(team["id"]))
                response["teams"].append(team_with_links)
            else:
                response["teams"].append(team)
    else:
        response["teams"] = result
    return jsonify(response), status_code

@team_bp.route("/", methods=["POST"])
@jwt_required()
@validate_json(TEAM_SCHEMA)
def create_team():
    """
    Creates a new team. Only authorized users can create a team.

    - **name**: The name of the team (required).
    - **description**: A description of the team (optional).
    - **lead_id**: The user ID of the team leader (required).

    Returns:
        - JSON representation of the newly created team.
        - HTTP Status Code: 201 (Created) on success.
        - HTTP Status Code: 500 (Internal Server Error) on failure.
    """
    user_id = get_jwt_identity()
    data = request.get_json()
    result, status_code = TeamService.create_team(user_id, data)
    cache_key = f"team_all_{user_id}"
    cache.delete(cache_key)
    if status_code == 201 and isinstance(result, dict) and "id" in result:
        result["_links"] = generate_team_hypermedia_links(team_id=str(result["id"]))
    return jsonify(result), status_code

@team_bp.route("/<team_id>", methods=["GET"])
@jwt_required()
@cache.cached(
    timeout=300, key_prefix=lambda: f"team_{get_jwt_identity()}_{request.view_args['team_id']}"
)
def get_team(team_id):
    """
    Retrieves details of a specific team by its ID.

    Args:
        - **team_id**: UUID of the team to retrieve.

    Returns:
        - JSON representation of the team if found.
        - HTTP Status Code: 200 (OK) on success.
        - HTTP Status Code: 404 (Not Found) if the team doesn't exist.
    """
    user_id = get_jwt_identity()
    result, status_code = TeamService.get_team(user_id, team_id)
    if status_code == 200 and isinstance(result, dict) and "id" in result:
        result["_links"] = generate_team_hypermedia_links(team_id=str(team_id))
    return jsonify(result), status_code

@team_bp.route("/<team_id>", methods=["PUT"])
@jwt_required()
@validate_json(TEAM_UPDATE_SCHEMA)
def update_team(team_id):
    """
    Updates an existing team's details.

    Args:
        - **team_id**: UUID of the team to update.

    Request Body:
        - **name**: The new name of the team (optional).
        - **description**: The new description of the team (optional).
        - **lead_id**: The new team leader's user ID (optional).

    Returns:
        - JSON representation of the updated team on success.
        - HTTP Status Code: 200 (OK).
        - HTTP Status Code: 404 (Not Found) if the team does not exist.
        - HTTP Status Code: 400 (Bad Request) if invalid data is provided.
    """
    user_id = get_jwt_identity()
    data = request.get_json()
    result, status_code = TeamService.update_team(user_id, team_id, data)
    cache_key = f"team_{user_id}_{team_id}"
    cache.delete(cache_key)
    all_teams_cache_key = f"team_all_{user_id}"
    cache.delete(all_teams_cache_key)
    if status_code == 200 and isinstance(result, dict) and "id" in result:
        result["_links"] = generate_team_hypermedia_links(team_id=str(team_id))
    return jsonify(result), status_code

@team_bp.route("/<team_id>", methods=["DELETE"])
@jwt_required()
def delete_team(team_id):
    """
    Deletes a team by its ID.

    Args:
        - **team_id**: UUID of the team to delete.

    Returns:
        - Success message if team is deleted.
        - HTTP Status Code: 200 (OK) on success.
        - HTTP Status Code: 404 (Not Found) if the team does not exist.
    """
    user_id = get_jwt_identity()
    result, status_code = TeamService.delete_team(user_id, team_id)
    team_id_str = str(team_id)
    cache_key = f"team_{user_id}_{team_id_str}"
    cache.delete(cache_key)
    all_teams_cache_key = f"team_all_{user_id}"
    cache.delete(all_teams_cache_key)
    team_members_cache_key = f"team_member_{user_id}_{team_id_str}"
    cache.delete(team_members_cache_key)
    if status_code == 200 and isinstance(result, dict):
        result["_links"] = generate_team_hypermedia_links()
    return jsonify(result), status_code

# ------------------ TEAM MEMBERSHIP ROUTES ------------------

@team_bp.route("/<team_id>/members", methods=["POST"])
@jwt_required()
@validate_json(TEAM_MEMBERSHIP_SCHEMA)
def add_team_member(team_id):
    """
    Adds a user to a team with a specified role.

    Args:
        - **team_id**: UUID of the team.
        - Request Body:
            - **user_id**: The user ID to add to the team (required).
            - **role**: The role the user will have in the team (required).

    Returns:
        - Success message if the user is added successfully.
        - HTTP Status Code: 201 (Created) on success.
        - HTTP Status Code: 400 (Bad Request) if the user is already a member of the team.
        - HTTP Status Code: 500 (Internal Server Error) on failure.
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()
    result, status_code = TeamService.add_team_member(current_user_id, team_id, data)
    team_id_str = str(team_id)
    cache_key = f"team_member_{current_user_id}_{team_id_str}"
    cache.delete(cache_key)
    team_cache_key = f"team_{current_user_id}_{team_id_str}"
    cache.delete(team_cache_key)
    if status_code == 201 and isinstance(result, dict) and "user_id" in data:
        user_id_str = str(data["user_id"])
        result["_links"] = generate_team_member_links(team_id_str, user_id_str)
    return jsonify(result), status_code

@team_bp.route("/<team_id>/members/<user_id>", methods=["PUT"])
@jwt_required()
@validate_json({"type": "object", "properties": {"role": {"type": "string"}}, "required": ["role"]})
def update_team_member(team_id, user_id):
    """
    Updates the role of a member in a team.

    Args:
        - **team_id**: UUID of the team.
        - **user_id**: UUID of the user whose role will be updated.
        - Request Body:
            - **role**: The new role for the user (required).

    Returns:
        - Success message if the role is updated.
        - HTTP Status Code: 200 (OK).
        - HTTP Status Code: 404 (Not Found) if the membership does not exist.
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()
    result, status_code = TeamService.update_team_member(current_user_id, team_id, user_id, data)
    team_id_str = str(team_id)
    cache_key = f"team_member_{current_user_id}_{team_id_str}"
    cache.delete(cache_key)
    if status_code == 200 and isinstance(result, dict):
        user_id_str = str(user_id)
        result["_links"] = generate_team_member_links(team_id_str, user_id_str)
    return jsonify(result), status_code

@team_bp.route("/<team_id>/members/<user_id>", methods=["DELETE"])
@jwt_required()
def remove_team_member(team_id, user_id):
    """
    Removes a user from a team.

    Args:
        - **team_id**: UUID of the team.
        - **user_id**: UUID of the user to be removed from the team.

    Returns:
        - Success message if the user is removed successfully.
        - HTTP Status Code: 200 (OK) on success.
        - HTTP Status Code: 404 (Not Found) if the membership does not exist.
    """
    current_user_id = get_jwt_identity()
    result, status_code = TeamService.remove_team_member(current_user_id, team_id, user_id)
    team_id_str = str(team_id)
    cache_key = f"team_member_{current_user_id}_{team_id_str}"
    cache.delete(cache_key)
    team_cache_key = f"team_{current_user_id}_{team_id_str}"
    cache.delete(team_cache_key)
    if status_code == 200 and isinstance(result, dict):
        result["_links"] = generate_team_member_links(team_id_str)
    return jsonify(result), status_code

@team_bp.route("/<team_id>/members", methods=["GET"])
@jwt_required()
@cache.cached(
    timeout=300,
    key_prefix=lambda: f"team_member_{get_jwt_identity()}_{request.view_args['team_id']}",
)
def get_team_members(team_id):
    """
    Retrieves all members of a specific team.

    Args:
        - **team_id**: UUID of the team whose members are to be retrieved.

    Returns:
        - List of members of the team, including their user IDs and roles.
        - HTTP Status Code: 200 (OK) on success.
        - HTTP Status Code: 404 (Not Found) if the team does not exist.
    """
    current_user_id = get_jwt_identity()
    result, status_code = TeamService.get_team_members(current_user_id, team_id)
    team_id_str = str(team_id)
    if status_code == 200 and isinstance(result, dict):
        if "team" in result and isinstance(result["team"], dict) and "id" in result["team"]:
            result["team"]["_links"] = generate_team_hypermedia_links(team_id=str(result["team"]["id"]), members=True)
        if "members" in result and isinstance(result["members"], list):
            for member in result["members"]:
                if isinstance(member, dict) and "user_id" in member:
                    member["_links"] = generate_team_member_links(team_id_str, str(member["user_id"]))
        result["_links"] = generate_team_member_links(team_id_str)
    return jsonify(result), status_code
