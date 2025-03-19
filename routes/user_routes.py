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
    return jsonify({'error': 'Bad Request', 'message': str(error)}), 400

@user_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found', 'message': str(error)}), 404

@user_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal Server Error', 'message': str(error)}), 500

# ------------------ USER ROUTES ------------------
@user_bp.route('/users', methods=['POST'])
@validate_json(USER_SCHEMA)
def create_user():
    """Create a new user."""
    try:
        data = request.get_json()
        hashed_password = generate_password_hash(data['password'])  # Hash the password
        new_user = User(
            username=data['username'],
            email=data['email'],
            password_hash=hashed_password,  # Use hashed password
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
    """Get user details."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict()), 200

@user_bp.route('/users/<uuid:user_id>', methods=['PUT'])
@jwt_required()
@validate_json(USER_SCHEMA)
def update_user(user_id):
    """Update user details."""
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
    """Delete a user."""
    current_user = User.query.get(get_jwt_identity())
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin privileges required'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'}), 200