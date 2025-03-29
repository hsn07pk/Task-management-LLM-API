# app.py
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_caching import Cache
from werkzeug.security import check_password_hash
from models import (
    db, init_db, create_user, get_all_users, update_user, delete_user,
    PriorityEnum, StatusEnum, User
)
from routes.task_routes import task_bp
from routes.team_routes import team_bp
from routes.project_routes import project_bp
from routes.user_routes import user_bp
from datetime import timedelta
from werkzeug.security import check_password_hash
from extentions.extensions import cache  # Import from extensions

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
    app.config['JWT_SECRET_KEY'] = 'super-secret'  # Secret key for JWT token encoding (change for production)
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)  # Token expiration time set to 1 hour
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # Cache expiry time set to 5 minutes (300 seconds)

    # Initialize JWT and Cache
    jwt = JWTManager(app)
    cache.init_app(app)  # Initialize caching with the Flask app
    
    # Initialize the database
    init_db(app)

    # Register Blueprints for modular routes
    app.register_blueprint(task_bp)
    app.register_blueprint(team_bp) 
    app.register_blueprint(project_bp)
    app.register_blueprint(user_bp)

    # ---------------- AUTHENTICATION ROUTES ----------------

    @app.route('/login', methods=['POST'])
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
        data = request.get_json()

        # Check if email and password are provided in the request
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Missing email or password'}), 400

        # Find user by email
        user = User.query.filter_by(email=data['email']).first()

        # Validate user and password
        if not user or not check_password_hash(user.password_hash, data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401

        # Generate JWT token upon successful login
        access_token = create_access_token(identity=str(user.user_id))
        return jsonify({'access_token': access_token}), 200

    # ---------------- ERROR HANDLERS ----------------

    @app.errorhandler(400)
    def bad_request(error):
        """
        Handle 400 Bad Request error. Returns a JSON response with the error details.

        Returns:
            JSON response with error message and status code 400.
        """
        return jsonify({'error': 'Bad Request', 'message': str(error)}), 400

    @app.errorhandler(404)
    def not_found(error):
        """
        Handle 404 Not Found error. Returns a JSON response with the error details.

        Returns:
            JSON response with error message and status code 404.
        """
        return jsonify({'error': 'Not Found', 'message': str(error)}), 404

    @app.errorhandler(500)
    def internal_error(error):
        """
        Handle 500 Internal Server Error. Returns a JSON response with the error details.

        Returns:
            JSON response with error message and status code 500.
        """
        return jsonify({'error': 'Internal Server Error', 'message': str(error)}), 500

    # ---------------- TEST ROUTE ----------------

    @app.route('/test', methods=['GET'])
    @jwt_required()  # Ensure the user is authenticated
    @cache.cached(timeout=600, key_prefix=lambda: f"test_operations_{get_jwt_identity()}")  # Cache per user
    def test_operations():
        """
        Test endpoint to check JWT authentication and caching functionality.

        Returns:
            JSON response with a message for the authenticated user.
        """
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({
            'message': f'Hello {user.username}, you are authenticated!',
            'user_id': current_user_id
        })

    # ---------------- CACHED USER FETCH ----------------

    @app.route('/users', methods=['GET'])
    @cache.cached(timeout=300, key_prefix='all_users')  # Cache results for 5 minutes
    def fetch_users():
        """
        Fetch all users from the database with caching enabled.

        Returns:
            JSON response containing a list of all users.
        """
        users = get_all_users()
        # Convert the list of User objects to a list of dictionaries using to_dict
        users_list = [user.to_dict() for user in users]
        return jsonify(users_list), 200

    return app

if __name__ == '__main__':
    """
    Main entry point for running the Flask application.

    When this script is executed directly, it runs the Flask development server
    in debug mode for testing and development.
    """
    app = create_app()
    app.run(debug=True)
