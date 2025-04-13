from flask import Blueprint, jsonify
from werkzeug.security import generate_password_hash

from models import User, db, get_all_users

user_bp = Blueprint("user_routes", __name__)


# ------------------ ERROR HANDLERS ------------------
@user_bp.errorhandler(400)
def bad_request(error):
    """
    Handles 400 Bad Request errors.

    :param error: The error message.
    :return: JSON response with error message and status code 400.
    """
    return jsonify({"error": "Bad Request", "message": str(error)}), 400


@user_bp.errorhandler(404)
def not_found(error):
    """
    Handles 404 Not Found errors.

    :param error: The error message.
    :return: JSON response with error message and status code 404.
    """
    return jsonify({"error": "Not Found", "message": str(error)}), 404


@user_bp.errorhandler(500)
def internal_error(error):
    """
    Handles 500 Internal Server errors.

    :param error: The error message.
    :return: JSON response with error message and status code 500.
    """
    return jsonify({"error": "Internal Server Error", "message": str(error)}), 500


class UserService:
    """
    Service class to encapsulate user operations.
    """

    @staticmethod
    def create_user(data):
        """
        Create a new user in the system.

        :param data: User data dictionary containing username, email, password, and optional role
        :return: Tuple of (user_dict, status_code) or (error_dict, status_code)
        """
        try:
            # Check if the email or username already exists
            if User.query.filter_by(email=data["email"]).first():
                return {"error": "Email already exists"}, 400
            if User.query.filter_by(username=data["username"]).first():
                return {"error": "Username already exists"}, 400

            hashed_password = generate_password_hash(data["password"])
            new_user = User(
                username=data["username"],
                email=data["email"],
                password_hash=hashed_password,
                role=data.get("role", "member"),
            )

            db.session.add(new_user)
            db.session.commit()
            return new_user.to_dict(), 201

        except KeyError as e:
            db.session.rollback()
            return {
                "error": "Missing required field",
                "message": f"Field {str(e)} is required",
            }, 400
        except Exception as e:
            db.session.rollback()
            return {"error": "Internal server error", "message": str(e)}, 500

    @staticmethod
    def get_user(user_id):
        """
        Get a user by their ID.

        :param user_id: UUID of the user to retrieve
        :return: Tuple of (user_dict, status_code) or (error_dict, status_code)
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {"error": "User not found"}, 404
            return user.to_dict(), 200
        except Exception as e:
            return {"error": "Internal server error", "message": str(e)}, 500

    @staticmethod
    def update_user(user_id, current_user_id, data):
        """
        Update a user's details.

        :param user_id: UUID of the user to update
        :param current_user_id: UUID of the current logged-in user
        :param data: Dictionary with updated user data
        :return: Tuple of (user_dict, status_code) or (error_dict, status_code)
        """
        try:
            # Verify current user exists
            current_user = User.query.get(current_user_id)
            if not current_user:
                return {"error": "Current user not found"}, 404

            user = User.query.get(user_id)
            if not user:
                return {"error": "User not found"}, 404

            if str(user.user_id) != current_user_id and current_user.role != "admin":
                return {"error": "Unauthorized"}, 403

            # Check if username already exists (if it's being updated)
            if "username" in data and data["username"] != user.username:
                if User.query.filter_by(username=data["username"]).first():
                    return {"error": "Username already exists"}, 400
                user.username = data["username"]

            # Check if email already exists (if it's being updated)
            if "email" in data and data["email"] != user.email:
                if User.query.filter_by(email=data["email"]).first():
                    return {"error": "Email already exists"}, 400
                user.email = data["email"]

            if "password" in data:
                user.password_hash = generate_password_hash(data["password"])

            if "role" in data and current_user.role == "admin":  # Only admins can change roles
                user.role = data["role"]

            db.session.commit()
            return user.to_dict(), 200

        except Exception as e:
            db.session.rollback()
            return {"error": "Internal server error", "message": str(e)}, 500

    @staticmethod
    def delete_user(user_id, current_user_id):
        """
        Delete a user from the system.

        :param user_id: UUID of the user to delete
        :param current_user_id: UUID of the current logged-in user
        :return: Tuple of (message_dict, status_code) or (error_dict, status_code)
        """
        try:
            # Verify current user exists
            current_user = User.query.get(current_user_id)
            if not current_user:
                return {"error": "Current user not found"}, 404

            if current_user.role != "admin":
                return {"error": "Admin privileges required"}, 403

            user = User.query.get(user_id)
            if not user:
                return {"error": "User not found"}, 404

            db.session.delete(user)
            db.session.commit()
            return {"message": "User deleted successfully"}, 200

        except Exception as e:
            db.session.rollback()
            return {"error": "Internal server error", "message": str(e)}, 500

    @staticmethod
    def get_all_users():
        """
        Fetch all users from the database.

        :return: Tuple of (users_list, status_code) or (error_dict, status_code)
        """
        try:
            users = get_all_users()

            if users is None:
                return {"error": "Failed to retrieve users"}, 500

            # Convert the list of User objects to a list of dictionaries using to_dict
            users_list = []
            for user in users:
                try:
                    users_list.append(user.to_dict())
                except Exception:
                    # Continue with other users if one fails to convert
                    continue

            return users_list, 200

        except Exception as e:
            return {"error": "Internal server error", "message": str(e)}, 500
