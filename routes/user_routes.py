from flask import Blueprint, jsonify, request, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from extentions.extensions import cache
from schemas.schemas import USER_SCHEMA, USER_UPDATE_SCHEMA
from services.user_services import UserService
from utils.hypermedia.link_builder import build_standard_links
from validators.validators import validate_json
from utils.hypermedia.user_hypermedia import generate_user_hypermedia_links


user_bp = Blueprint(
    "user_routes", __name__, url_prefix="/users"
)

@user_bp.route("/", methods=["POST"])
@validate_json(USER_SCHEMA)
def create_user():
    """
    Create a new user in the system.

    This endpoint allows the creation of a new user. It checks for the uniqueness of
    email and username, hashes the password before saving, and assigns a default role
    of 'member' if not provided.

    :return: JSON response with the newly created user details or an error message.
    :status 201: Successfully created user.
    :status 400: Email or username already exists.
    :status 500: Internal server error.
    """
    data = request.get_json()
    result, status_code = UserService.create_user(data)
    if status_code == 201 and "id" in result:
        result["_links"] = generate_user_hypermedia_links(user_id=result["id"])
    return jsonify(result), status_code

@user_bp.route("/<user_id>", methods=["GET"])
@jwt_required()
@cache.cached(
    timeout=300, key_prefix=lambda: f"user_{get_jwt_identity()}_{request.view_args['user_id']}"
)
def get_user(user_id):
    """
    Get the details of a user by their ID.

    This endpoint retrieves the details of a specific user, identified by their user ID.
    The response is cached for 5 minutes for performance optimization.

    :param user_id: The UUID of the user to retrieve.
    :return: JSON response with the user's details or an error message.
    :status 200: Successfully retrieved user details.
    :status 404: User not found.
    """
    result, status_code = UserService.get_user(user_id)
    if status_code == 200:
        result["_links"] = generate_user_hypermedia_links(user_id=user_id)
    return jsonify(result), status_code

@user_bp.route("/<user_id>", methods=["PUT"])
@jwt_required()
@validate_json(USER_UPDATE_SCHEMA)
def update_user(user_id):
    """
    Update a user's details.

    This endpoint allows users to update their details such as username, email,
    password, and role (only if the user is an admin). It ensures that the current
    user is authorized to make the changes (i.e., they can only update their own details
    unless they are an admin).

    :param user_id: The UUID of the user to update.
    :return: JSON response with the updated user details or an error message.
    :status 200: Successfully updated user details.
    :status 400: Invalid input data.
    :status 403: Unauthorized access (if user tries to update someone else's details).
    :status 404: User not found.
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()
    result, status_code = UserService.update_user(user_id, current_user_id, data)
    cache_key = f"user_{current_user_id}_{user_id}"
    cache.delete(cache_key)
    if status_code == 200:
        result["_links"] = generate_user_hypermedia_links(user_id=user_id)
    return jsonify(result), status_code

@user_bp.route("/<user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    """
    Delete a user from the system.

    This endpoint allows an admin to delete a user. Only users with 'admin' role are
    allowed to perform this operation.

    :param user_id: The UUID of the user to delete.
    :return: JSON response indicating the success of the operation or an error message.
    :status 200: Successfully deleted the user.
    :status 403: Admin privileges required.
    :status 404: User not found.
    """
    current_user_id = get_jwt_identity()
    result, status_code = UserService.delete_user(user_id, current_user_id)
    if status_code == 200:
        result["_links"] = generate_user_hypermedia_links()
    return jsonify(result), status_code

@user_bp.route("/", methods=["GET"])
@cache.cached(timeout=200, key_prefix="all_users")
def fetch_users():
    """
    Fetch all users from the database with caching enabled.

    Returns:
        JSON response containing a list of all users and hypermedia controls.
    """
    result, status_code = UserService.get_all_users()
    response = {
        "users": [],
        "_links": generate_user_hypermedia_links()
    }
    if isinstance(result, list):
        for user in result:
            if isinstance(user, dict) and "id" in user:
                user_with_links = dict(user)
                user_with_links["_links"] = generate_user_hypermedia_links(user_id=user["id"])
                response["users"].append(user_with_links)
            else:
                response["users"].append(user)
    else:
        response["users"] = result
    return jsonify(response), status_code