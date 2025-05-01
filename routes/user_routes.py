from flask import Blueprint, jsonify, request, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from extentions.extensions import cache
from schemas.schemas import USER_SCHEMA, USER_UPDATE_SCHEMA
from services.user_services import UserService
from utils.hypermedia.link_builder import build_standard_links
from validators.validators import validate_json
from utils.hypermedia.user_hypermedia import generate_user_hypermedia_links, generate_users_collection_links, add_user_hypermedia_links


user_bp = Blueprint(
    "user_routes", __name__, url_prefix="/users"
)

@user_bp.errorhandler(400)
def bad_request(error):
    response = {
        "error": "Bad Request", 
        "message": str(error),
        "_links": generate_users_collection_links()
    }
    return jsonify(response), 400

@user_bp.errorhandler(404)
def not_found(error):
    response = {
        "error": "Not Found", 
        "message": str(error),
        "_links": generate_users_collection_links()
    }
    return jsonify(response), 404

@user_bp.errorhandler(500)
def internal_error(error):
    response = {
        "error": "Internal Server Error", 
        "message": str(error),
        "_links": generate_users_collection_links()
    }
    return jsonify(response), 500

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
    try:
        data = request.get_json()
        result, status_code = UserService.create_user(data)
        
        # Success case with valid user data
        if status_code == 201 and isinstance(result, dict) and "id" in result:
            # Add hypermedia links
            result = add_user_hypermedia_links(result)
            
            # Add location header for the created resource
            response = jsonify(result)
            response.headers['Location'] = url_for('user_routes.get_user', user_id=result['id'], _external=True)
            return response, 201
        
        # Handle error responses with proper status code
        elif isinstance(result, dict):
            if "_links" not in result:
                result["_links"] = generate_users_collection_links()
            return jsonify(result), status_code
        
        # Handle string responses or other non-dict responses
        elif result is not None:
            response = {
                "message": result if isinstance(result, str) else "Operation completed",
                "_links": generate_users_collection_links()
            }
            return jsonify(response), status_code
        
        # Fallback for unexpected response format
        else:
            response = {
                "error": "Unexpected response format from user service",
                "message": "The user service returned data in an unexpected format",
                "_links": generate_users_collection_links()
            }
            return jsonify(response), 500
    except Exception as e:
        response = {
            "error": "Internal server error", 
            "message": str(e),
            "_links": generate_users_collection_links()
        }
        return jsonify(response), 500

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
    try:
        result, status_code = UserService.get_user(user_id)
        
        # Success case with valid user data
        if status_code == 200 and isinstance(result, dict) and "id" in result:
            # Add hypermedia links
            result = add_user_hypermedia_links(result)
            return jsonify(result), 200
        
        # Handle error responses with proper status code
        elif isinstance(result, dict):
            if "_links" not in result:
                result["_links"] = generate_users_collection_links()
            return jsonify(result), status_code
        
        # Handle string responses or other non-dict responses
        elif result is not None:
            response = {
                "message": result if isinstance(result, str) else "Operation completed",
                "_links": generate_users_collection_links()
            }
            return jsonify(response), status_code
            
        # Fallback for unexpected response format
        else:
            response = {
                "error": "Unexpected response format from user service",
                "message": f"Failed to retrieve user with ID {user_id}",
                "_links": generate_users_collection_links()
            }
            return jsonify(response), 500
    except Exception as e:
        response = {
            "error": "Internal server error", 
            "message": str(e),
            "_links": generate_users_collection_links()
        }
        return jsonify(response), 500

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
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Check if user exists first
        user_result, user_status = UserService.get_user(user_id)
        if user_status != 200:
            response = {
                "error": "User not found",
                "message": f"User with ID {user_id} not found",
                "_links": generate_users_collection_links()
            }
            return jsonify(response), 404
            
        result, status_code = UserService.update_user(user_id, current_user_id, data)
        
        # Clear cache
        cache_key = f"user_{current_user_id}_{user_id}"
        cache.delete(cache_key)
        all_users_cache_key = f"all_users_{current_user_id}"
        cache.delete(all_users_cache_key)
        
        # Success case with valid user data
        if status_code == 200 and isinstance(result, dict) and "id" in result:
            # Add hypermedia links
            result = add_user_hypermedia_links(result)
            return jsonify(result), 200
        
        # Handle error responses with proper status code
        elif isinstance(result, dict):
            if "_links" not in result:
                result["_links"] = generate_users_collection_links()
            return jsonify(result), status_code
        
        # Handle string responses or other non-dict responses
        elif result is not None:
            response = {
                "message": result if isinstance(result, str) else "Operation completed",
                "_links": generate_users_collection_links()
            }
            return jsonify(response), status_code
            
        # Fallback for unexpected response format
        else:
            response = {
                "error": "Unexpected response format from user service",
                "message": f"Failed to update user with ID {user_id}",
                "_links": generate_users_collection_links()
            }
            return jsonify(response), 500
    except Exception as e:
        response = {
            "error": "Internal server error", 
            "message": str(e),
            "_links": generate_users_collection_links()
        }
        return jsonify(response), 500

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
    try:
        current_user_id = get_jwt_identity()
        
        # Check if user exists first
        user_result, user_status = UserService.get_user(user_id)
        if user_status != 200:
            response = {
                "error": "User not found",
                "message": f"User with ID {user_id} not found",
                "_links": generate_users_collection_links()
            }
            return jsonify(response), 404
            
        result, status_code = UserService.delete_user(user_id, current_user_id)
        
        # Clear cache
        user_cache_key = f"user_{current_user_id}_{user_id}"
        cache.delete(user_cache_key)
        all_users_cache_key = f"all_users_{current_user_id}"
        cache.delete(all_users_cache_key)
        
        # Success case
        if status_code == 200:
            response = {
                "message": result if isinstance(result, str) else "User deleted successfully",
                "_links": generate_users_collection_links()
            }
            return jsonify(response), 200
        
        # Handle error responses with proper status code
        elif isinstance(result, dict):
            if "_links" not in result:
                result["_links"] = generate_users_collection_links()
            return jsonify(result), status_code
        
        # Handle string responses or other non-dict responses that aren't success
        elif result is not None and status_code != 200:
            response = {
                "message": result if isinstance(result, str) else "Operation completed",
                "_links": generate_users_collection_links()
            }
            return jsonify(response), status_code
            
        # Fallback for unexpected response format
        else:
            response = {
                "error": "Unexpected response format from user service",
                "message": f"Failed to delete user with ID {user_id}",
                "_links": generate_users_collection_links()
            }
            return jsonify(response), 500
    except Exception as e:
        response = {
            "error": "Internal server error", 
            "message": str(e),
            "_links": generate_users_collection_links()
        }
        return jsonify(response), 500

@user_bp.route("/", methods=["GET"])
@jwt_required()
@cache.cached(timeout=200, key_prefix=lambda: f"all_users_{get_jwt_identity()}")
def fetch_users():
    """
    Fetch all users from the database with caching enabled.

    Returns:
        JSON response containing a list of all users and hypermedia controls.
    """
    try:
        result, status_code = UserService.get_all_users()
        
        # Success case with list of users
        if status_code == 200 and isinstance(result, list):
            response = {
                "users": [],
                "_links": generate_users_collection_links()
            }
            
            for user in result:
                if isinstance(user, dict) and "id" in user:
                    response["users"].append(add_user_hypermedia_links(user))
                else:
                    # Handle non-standard user objects in the list
                    response["users"].append(user)
            return jsonify(response), 200
        
        # Handle error responses with proper status code
        elif isinstance(result, dict):
            if "_links" not in result:
                result["_links"] = generate_users_collection_links()
            return jsonify(result), status_code
        
        # Handle string responses or other non-dict responses
        elif result is not None:
            response = {
                "message": result if isinstance(result, str) else "Operation completed",
                "_links": generate_users_collection_links()
            }
            return jsonify(response), status_code
            
        # Fallback for unexpected response format
        else:
            response = {
                "error": "Unexpected response format from user service",
                "message": "Failed to fetch users",
                "_links": generate_users_collection_links()
            }
            return jsonify(response), 500
    except Exception as e:
        response = {
            "error": "Internal server error", 
            "message": str(e),
            "_links": generate_users_collection_links()
        }
        return jsonify(response), 500