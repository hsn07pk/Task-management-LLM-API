from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, db
from werkzeug.security import generate_password_hash
from validators.validators import validate_json
from schemas.schemas import USER_SCHEMA
from extentions.extensions import cache

user_bp = Blueprint('user_routes', __name__)

# ------------------ ERROR HANDLERS ------------------
@user_bp.errorhandler(400)
def bad_request(error):
    """
    Handles 400 Bad Request errors.
    
    :param error: The error message.
    :return: JSON response with error message and status code 400.
    """
    return jsonify({'error': 'Bad Request', 'message': str(error)}), 400

@user_bp.errorhandler(404)
def not_found(error):
    """
    Handles 404 Not Found errors.
    
    :param error: The error message.
    :return: JSON response with error message and status code 404.
    """
    return jsonify({'error': 'Not Found', 'message': str(error)}), 404

@user_bp.errorhandler(500)
def internal_error(error):
    """
    Handles 500 Internal Server errors.
    
    :param error: The error message.
    :return: JSON response with error message and status code 500.
    """
    return jsonify({'error': 'Internal Server Error', 'message': str(error)}), 500

# ------------------ USER ROUTES ------------------
@user_bp.route('/users', methods=['POST'])
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
        
        # Check if the email or username already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400

        hashed_password = generate_password_hash(data['password'])
        new_user = User(
            username=data['username'],
            email=data['email'],
            password_hash=hashed_password,
            role=data.get('role', 'member')
        )
        
        db.session.add(new_user)
        db.session.commit()
        return jsonify(new_user.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@user_bp.route('/users/<uuid:user_id>', methods=['GET'])
@jwt_required()
@cache.cached(timeout=300, key_prefix=lambda: f"user_{get_jwt_identity()}")
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
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict()), 200

@user_bp.route('/users/<uuid:user_id>', methods=['PUT'])
@jwt_required()
@validate_json(USER_SCHEMA)
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
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    if str(user.user_id) != current_user_id and user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    if 'username' in data:
        user.username = data['username']
    if 'email' in data:
        user.email = data['email']
    if 'password' in data:
        user.password_hash = generate_password_hash(data['password'])
    if 'role' in data and user.role == 'admin':  # Only admins can change roles
        user.role = data['role']

    db.session.commit()
    return jsonify(user.to_dict()), 200

@user_bp.route('/users/<uuid:user_id>', methods=['DELETE'])
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
    current_user = User.query.get(get_jwt_identity())
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin privileges required'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'}), 200
