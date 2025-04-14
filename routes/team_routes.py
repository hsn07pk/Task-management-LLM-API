from flask import Blueprint, jsonify, request, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required

from extentions.extensions import cache
from schemas.schemas import TEAM_MEMBERSHIP_SCHEMA, TEAM_SCHEMA, TEAM_UPDATE_SCHEMA
from services.team_services import TeamService
from validators.validators import validate_json

# Blueprint for team-related routes
team_bp = Blueprint("team_routes", __name__, url_prefix="/teams")


def add_hypermedia_links(team, members=False):
    """
    Add hypermedia links to a team resource.

    Args:
        team (dict): The team dictionary to add links to
        members (bool): Whether to include links to team member resources

    Returns:
        dict: The team with added _links property
    """
    if not team or not isinstance(team, dict) or "id" not in team:
        return team

    # Create a deep copy of the team to avoid modifying the original
    team_with_links = dict(team)

    # Convert team_id to string to ensure URL generation works correctly
    team_id = str(team["id"])

    # Add links for the team resource
    team_with_links["_links"] = {
        "self": {"href": url_for("team_routes.get_team", team_id=team_id, _external=True)},
        "update": {"href": url_for("team_routes.update_team", team_id=team_id, _external=True)},
        "delete": {"href": url_for("team_routes.delete_team", team_id=team_id, _external=True)},
        "members": {
            "href": url_for("team_routes.get_team_members", team_id=team_id, _external=True)
        },
        "collection": {"href": url_for("team_routes.get_all_teams", _external=True)},
    }

    # If this is a members response, add member-specific links
    if members:
        team_with_links["_links"]["add_member"] = {
            "href": url_for("team_routes.add_team_member", team_id=team_id, _external=True)
        }

    return team_with_links


def add_member_hypermedia_links(team_id, member):
    """
    Add hypermedia links to a team member resource.

    Args:
        team_id (str): The team ID
        member (dict): The member dictionary to add links to

    Returns:
        dict: The member with added _links property
    """
    if not member or not isinstance(member, dict) or "user_id" not in member:
        return member

    # Create a deep copy of the member to avoid modifying the original
    member_with_links = dict(member)

    # Ensure IDs are strings for URL generation
    team_id = str(team_id)
    user_id = str(member["user_id"])

    # Add links for the member resource
    member_with_links["_links"] = {
        "team": {"href": url_for("team_routes.get_team", team_id=team_id, _external=True)},
        "update": {
            "href": url_for(
                "team_routes.update_team_member", team_id=team_id, user_id=user_id, _external=True
            )
        },
        "delete": {
            "href": url_for(
                "team_routes.remove_team_member", team_id=team_id, user_id=user_id, _external=True
            )
        },
        "collection": {
            "href": url_for("team_routes.get_team_members", team_id=team_id, _external=True)
        },
    }

    return member_with_links


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

    # Add hypermedia links to each team in the list
    if status_code == 200 and isinstance(result, list):
        result = [add_hypermedia_links(team) for team in result]

    return jsonify(result), status_code


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

    # Invalidate the cache
    cache_key = f"team_all_{user_id}"
    cache.delete(cache_key)

    # Add hypermedia links if team creation was successful
    if status_code == 201 and isinstance(result, dict) and "id" in result:
        result = add_hypermedia_links(result)

    return jsonify(result), status_code


@team_bp.route("/<uuid:team_id>", methods=["GET"])
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

    # Add hypermedia links if team was found
    if status_code == 200 and isinstance(result, dict) and "id" in result:
        result = add_hypermedia_links(result)

    return jsonify(result), status_code


@team_bp.route("/<uuid:team_id>", methods=["PUT"])
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

    # Invalidate the cache for this team
    cache_key = f"team_{user_id}_{team_id}"
    cache.delete(cache_key)

    # Also invalidate the all teams cache
    all_teams_cache_key = f"team_all_{user_id}"
    cache.delete(all_teams_cache_key)

    # Add hypermedia links if update was successful
    if status_code == 200 and isinstance(result, dict) and "id" in result:
        result = add_hypermedia_links(result)

    return jsonify(result), status_code


@team_bp.route("/<uuid:team_id>", methods=["DELETE"])
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

    # Invalidate relevant caches
    cache_key = f"team_{user_id}_{team_id}"
    cache.delete(cache_key)
    all_teams_cache_key = f"team_all_{user_id}"
    cache.delete(all_teams_cache_key)
    team_members_cache_key = f"team_member_{user_id}_{team_id}"
    cache.delete(team_members_cache_key)

    # Add link to teams collection after deletion
    if status_code == 200 and isinstance(result, dict):
        result["_links"] = {"teams": {"href": url_for("team_routes.get_all_teams", _external=True)}}

    return jsonify(result), status_code


# ------------------ TEAM MEMBERSHIP ROUTES ------------------


@team_bp.route("/<uuid:team_id>/members", methods=["POST"])
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

    # Invalidate the cache for this team's members
    team_id_str = str(team_id)
    cache_key = f"team_member_{current_user_id}_{team_id_str}"
    cache.delete(cache_key)

    # Also invalidate the team details cache
    team_cache_key = f"team_{current_user_id}_{team_id_str}"
    cache.delete(team_cache_key)

    # Add hypermedia links if member was added successfully
    if status_code == 201 and isinstance(result, dict) and "user_id" in data:
        user_id_str = str(data["user_id"])
        result["_links"] = {
            "team": {"href": url_for("team_routes.get_team", team_id=team_id_str, _external=True)},
            "members": {
                "href": url_for("team_routes.get_team_members", team_id=team_id_str, _external=True)
            },
            "member": {
                "href": url_for(
                    "team_routes.update_team_member",
                    team_id=team_id_str,
                    user_id=user_id_str,
                    _external=True,
                )
            },
        }

    return jsonify(result), status_code


@team_bp.route("/<uuid:team_id>/members/<uuid:user_id>", methods=["PUT"])
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

    # Invalidate the cache for this team's members
    team_id_str = str(team_id)
    cache_key = f"team_member_{current_user_id}_{team_id_str}"
    cache.delete(cache_key)

    # Add hypermedia links if update was successful
    if status_code == 200 and isinstance(result, dict):
        user_id_str = str(user_id)
        result["_links"] = {
            "team": {"href": url_for("team_routes.get_team", team_id=team_id_str, _external=True)},
            "members": {
                "href": url_for("team_routes.get_team_members", team_id=team_id_str, _external=True)
            },
            "delete": {
                "href": url_for(
                    "team_routes.remove_team_member",
                    team_id=team_id_str,
                    user_id=user_id_str,
                    _external=True,
                )
            },
        }

    return jsonify(result), status_code


@team_bp.route("/<uuid:team_id>/members/<uuid:user_id>", methods=["DELETE"])
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

    # Invalidate the cache for this team's members
    team_id_str = str(team_id)
    cache_key = f"team_member_{current_user_id}_{team_id_str}"
    cache.delete(cache_key)

    # Also invalidate the team details cache
    team_cache_key = f"team_{current_user_id}_{team_id_str}"
    cache.delete(team_cache_key)

    # Add hypermedia links if deletion was successful
    if status_code == 200 and isinstance(result, dict):
        result["_links"] = {
            "team": {"href": url_for("team_routes.get_team", team_id=team_id_str, _external=True)},
            "members": {
                "href": url_for("team_routes.get_team_members", team_id=team_id_str, _external=True)
            },
            "add_member": {
                "href": url_for("team_routes.add_team_member", team_id=team_id_str, _external=True)
            },
        }

    return jsonify(result), status_code


@team_bp.route("/<uuid:team_id>/members", methods=["GET"])
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

    # Add hypermedia links to each member and to the response
    if status_code == 200 and isinstance(result, dict):
        team_id_str = str(team_id)

        # Add links to each member if they exist
        if "members" in result and isinstance(result["members"], list):
            result["members"] = [
                add_member_hypermedia_links(team_id_str, member) for member in result["members"]
            ]

        # Add team links if team info exists
        if "team" in result and isinstance(result["team"], dict) and "id" in result["team"]:
            result["team"] = add_hypermedia_links(result["team"], members=True)

        # Add collection links
        result["_links"] = {
            "team": {"href": url_for("team_routes.get_team", team_id=team_id_str, _external=True)},
            "add_member": {
                "href": url_for("team_routes.add_team_member", team_id=team_id_str, _external=True)
            },
        }

    return jsonify(result), status_code
