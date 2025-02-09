from flask import Flask
from models import db, init_db, create_user, get_all_users, update_user, delete_user

def create_app():
    app = Flask(__name__)
    init_db(app)
    
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
