import pytest
import json
from app import create_app
from models import db, User
from werkzeug.security import generate_password_hash

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'JWT_SECRET_KEY': 'test-secret-key'
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_login_flow(client):
    """Test the complete login flow."""
    # Create a test user
    with client.application.app_context():
        user = User(
            username='authuser',
            email='auth@example.com',
            password_hash=generate_password_hash('securepass')
        )
        db.session.add(user)
        db.session.commit()
    
    # Login
    login_response = client.post('/login', json={
        'email': 'auth@example.com',
        'password': 'securepass'
    })
    assert login_response.status_code == 200
    token = json.loads(login_response.data)['access_token']
    
    # Use token to access protected route
    test_response = client.get('/test', headers={
        'Authorization': f'Bearer {token}'
    })
    assert test_response.status_code == 200
    assert 'authuser' in json.loads(test_response.data)['message']

def test_invalid_token(client):
    """Test accessing protected route with invalid token.""" 
    response = client.get('/test', headers={
        'Authorization': 'Bearer invalid-token'
    })
    assert response.status_code == 422  # JWT decode error
