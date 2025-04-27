# app.py
from datetime import timedelta

from flasgger import Swagger
from flask import Flask, jsonify, request
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from werkzeug.security import check_password_hash

from extentions.extensions import cache  # Import from extensions
from models import User, init_db
from routes.project_routes import project_bp
from routes.task_routes import task_bp
from routes.team_routes import team_bp
from routes.user_routes import user_bp
from blueprints.entry_point import entry_bp


def create_app():
    """
    Create and configure the Flask application.
    This function sets up the application, including JWT authentication, caching,
    database initialization, and routing for various modules such as tasks, teams,
    projects, and users.
    Returns:
        Flask app instance
    """
    app = Flask(__name__)
    # Application configuration
    app.config["JWT_SECRET_KEY"] = (
        "super-secret"  # Secret key for JWT token encoding (change for production)
    )
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(
        hours=1
    )  # Token expiration time set to 1 hour
    app.config["CACHE_DEFAULT_TIMEOUT"] = 300  # Cache expiry time set to 5 minutes (300 seconds)
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "postgresql://postgres:postgres@localhost:5432/taskmanagement"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # Initialize JWT and Cache
    jwt = JWTManager(app)  # Store the JWT instance
    cache.init_app(app)  # Initialize caching with the Flask app
    # Initialize the database
    init_db(app)
    # Register Blueprints for modular routes
    app.register_blueprint(entry_bp)  # Register the entry point blueprint first
    app.register_blueprint(task_bp)
    app.register_blueprint(team_bp)
    app.register_blueprint(project_bp)
    app.register_blueprint(user_bp)
    app.config["SWAGGER"] = {
        "title": "Task Management API",
        "openapi": "3.0.4",
        "uiversion": 3,
    }
    swagger = Swagger(app, template_file="doc/openapi.yml")
    # Register authentication routes
    register_auth_routes(app)
    # Register error handlers
    register_error_handlers(app)
    # Register test route
    register_test_route(app)
    return app

def register_auth_routes(app):
    """Register authentication-related routes with the Flask app."""
    @app.route("/login", methods=["POST"])
    def login():
        """
        User login route. This route accepts email and password, and returns a JWT
        token if credentials are valid.
        Request body:
            {
                "email": "user_email",
                "password": "user_password"
            }
        Returns:
            JSON response containing the access token or an error message.
        """
        try:
            data = request.get_json()
            # Check if email and password are provided in the request
            if not data:
                return jsonify({"error": "Missing request body"}), 400
            if "email" not in data:
                return jsonify({"error": "Email is required"}), 400
            if "password" not in data:
                return jsonify({"error": "Password is required"}), 400
            # Find user by email
            user = User.query.filter_by(email=data["email"]).first()
            # Validate user and password
            if not user:
                return jsonify({"error": "User not found"}), 401
            if not check_password_hash(user.password_hash, data["password"]):
                return jsonify({"error": "Invalid password"}), 401
            # Generate JWT token upon successful login
            access_token = create_access_token(identity=str(user.user_id))
            
            # Add hypermedia links for authenticated routes
            response = {
                "access_token": access_token,
                "user_id": str(user.user_id),
                "username": user.username,
                "_links": {
                    "self": {"href": url_for("login", _external=True)},
                    "user_profile": {"href": url_for("user_routes.get_user", user_id=user.user_id, _external=True)},
                    "tasks": {"href": url_for("task_routes.get_tasks", _external=True)},
                    "teams": {"href": url_for("team_routes.get_all_teams", _external=True)},
                    "projects": {"href": url_for("project_routes.get_all_projects", _external=True)},
                    "test": {"href": url_for("test_operations", _external=True)}
                }
            }
            return jsonify(response), 200
        except Exception as e:
            return jsonify({"error": "Internal server error", "message": str(e)}), 500

def register_error_handlers(app):
    """Register error handlers with the Flask app."""

    @app.errorhandler(400)
    def bad_request(error):
        """
        Handle 400 Bad Request error. Returns a JSON response with the error details.

        Returns:
            JSON response with error message and status code 400.
        """
        return jsonify({"error": "Bad Request", "message": str(error)}), 400

    @app.errorhandler(404)
    def not_found(error):
        """
        Handle 404 Not Found error. Returns a JSON response with the error details.

        Returns:
            JSON response with error message and status code 404.
        """
        return jsonify({"error": "Not Found", "message": str(error)}), 404

    @app.errorhandler(500)
    def internal_error(error):
        """
        Handle 500 Internal Server Error. Returns a JSON response with the error details.

        Returns:
            JSON response with error message and status code 500.
        """
        return jsonify({"error": "Internal Server Error", "message": str(error)}), 500


def register_test_route(app):
    """Register the test route with the Flask app."""

    @app.route("/test", methods=["GET"])
    @jwt_required()  # Ensure the user is authenticated
    @cache.cached(
        timeout=600, key_prefix=lambda: f"test_operations_{get_jwt_identity()}"
    )  # Cache per user
    def test_operations():
        """
        Test endpoint to check JWT authentication and caching functionality.

        Returns:
            JSON response with a message for the authenticated user.
        """
        try:
            current_user_id = get_jwt_identity()

            # Handle invalid UUID format
            try:
                user = User.query.get(current_user_id)
            except Exception as e:
                return jsonify({"error": "Invalid user ID format", "message": str(e)}), 400

            if not user:
                return jsonify({"error": "User not found"}), 404

            return jsonify(
                {
                    "message": f"Hello {user.username}, you are authenticated!",
                    "user_id": current_user_id,
                }
            )

        except Exception as e:
            return jsonify({"error": "Internal server error", "message": str(e)}), 500


if __name__ == "__main__":
    """
    Main entry point for running the Flask application.

    When this script is executed directly, it runs the Flask development server
    in debug mode for testing and development.
    """
    app = create_app()
    app.run(debug=True)
