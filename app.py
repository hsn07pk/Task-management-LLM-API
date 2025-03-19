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
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this in production
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)  # Token expiration time
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # Cache expiry time (5 minutes)
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True
    }
    app.config['SQLALCHEMY_DATABASE_URI'] = (
    'postgresql+psycopg2://admin:helloworld123@localhost:5432/task_management_db'
    )

    jwt = JWTManager(app)
    cache.init_app(app)  # Initialize caching with the app
    init_db(app)

    # Register blueprints
    app.register_blueprint(task_bp)
    app.register_blueprint(team_bp) 
    app.register_blueprint(project_bp)
    app.register_blueprint(user_bp)

    # ---------------- AUTHENTICATION ROUTES ----------------

    @app.route('/login', methods=['POST'])
    def login():
        data = request.get_json()
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Missing email or password'}), 400

        user = User.query.filter_by(email=data['email']).first()

        if not user or not check_password_hash(user.password_hash, data['password']):  # Correct password check
            return jsonify({'error': 'Invalid credentials'}), 401

        access_token = create_access_token(identity=str(user.user_id))
        return jsonify({'access_token': access_token}), 200

    # ---------------- ERROR HANDLERS ----------------

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad Request', 'message': str(error)}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not Found', 'message': str(error)}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal Server Error', 'message': str(error)}), 500

    # ---------------- TEST ROUTE ----------------

    @app.route('/test', methods=['GET'])
    @jwt_required()
    @cache.cached(timeout=600, key_prefix=lambda: f"test_operations_{get_jwt_identity()}")  # Cache per user
    def test_operations():
        """Test endpoint to check authentication & caching."""
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
        """Fetch all users with caching."""
        users = get_all_users()
        # Convert the list of User objects to a list of dictionaries using to_dict
        users_list = [user.to_dict() for user in users]
        return jsonify(users_list), 200

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
