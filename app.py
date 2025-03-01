from flask import Flask, request, jsonify
from models import (
    db, init_db, create_user, get_all_users, update_user, delete_user,
    PriorityEnum, StatusEnum
)
from routes.task_routes import task_bp
from datetime import datetime
from uuid import UUID

def create_app():
    app = Flask(__name__)
    init_db(app)
    
    # Register blueprints
    app.register_blueprint(task_bp)

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad Request', 'message': str(error)}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not Found', 'message': str(error)}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal Server Error', 'message': str(error)}), 500

    @app.route('/test')
    def test_operations():
        # Create Users
        user1 = create_user('hassan', 'hassan@example.com', 'hashed_password_1aa', 'admin')
        user2 = create_user('boba', 'boba@example.com', 'hashed_password_2aa', 'member')
        
        # Fetch Users
        users = get_all_users()
        user_list = [f"{user.username} ({user.email})" for user in users]
        
        # Update a user
        update_user(user1.user_id, username='alice_updated')
        
        # Delete a user
        delete_user(user2.user_id)
        
        return f"Users in DB: {', '.join(user_list)}"

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
