import json
import uuid
from unittest.mock import MagicMock, patch

import pytest
from werkzeug.security import check_password_hash, generate_password_hash

from models import User, db
from services.user_services import UserService


@pytest.fixture(scope="session")
def app():
    """
    Configure a Flask app for testing with PostgreSQL.
    """
    from app import create_app

    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "postgresql://admin:helloworld123@localhost/task_management_db",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "JWT_SECRET_KEY": "test-secret-key",
        }
    )

    return app


@pytest.fixture(scope="function")
def client(app):
    """
    Fixture to create a test client for the app.
    """
    with app.test_client() as testing_client:
        with app.app_context():
            yield testing_client


@pytest.fixture(scope="function")
def test_user(app):
    """
    Fixture to create a regular test user.
    """
    with app.app_context():
        user = User(
            username=f"testuser_{uuid.uuid4().hex[:8]}",
            email=f"testuser_{uuid.uuid4().hex[:8]}@example.com",
            password_hash=generate_password_hash("password123"),
            role="member",
        )
        db.session.add(user)
        db.session.commit()
        return {"id": str(user.user_id), "username": user.username, "email": user.email}


@pytest.fixture(scope="function")
def test_admin(app):
    """
    Fixture to create an admin test user.
    """
    with app.app_context():
        admin = User(
            username=f"admin_{uuid.uuid4().hex[:8]}",
            email=f"admin_{uuid.uuid4().hex[:8]}@example.com",
            password_hash=generate_password_hash("adminpass"),
            role="admin",
        )
        db.session.add(admin)
        db.session.commit()
        return {"id": str(admin.user_id), "username": admin.username, "email": admin.email}


def test_create_user_service(app):
    """
    Test the UserService.create_user method.
    """
    with app.app_context():
        data = {
            "username": f"newuser_{uuid.uuid4().hex[:8]}",
            "email": f"newuser_{uuid.uuid4().hex[:8]}@example.com",
            "password": "securepassword",
            "role": "member",
        }

        result, status_code = UserService.create_user(data)

        assert status_code == 201
        assert "user_id" in result
        assert result["username"] == data["username"]
        assert result["email"] == data["email"]
        assert result["role"] == "member"


def test_create_user_duplicate_email(app, test_user):
    """
    Test the UserService.create_user method with duplicate email.
    """
    with app.app_context():
        data = {
            "username": "anotheruser",
            "email": test_user["email"],  # Duplicate email
            "password": "password123",
            "role": "member",
        }

        result, status_code = UserService.create_user(data)

        assert status_code == 400
        assert "error" in result
        assert "Email already exists" in result["error"]


def test_create_user_duplicate_username(app, test_user):
    """
    Test the UserService.create_user method with duplicate username.
    """
    with app.app_context():
        data = {
            "username": test_user["username"],  # Duplicate username
            "email": "new1@example.com",
            "password": "password123",
            "role": "member",
        }

        result, status_code = UserService.create_user(data)

        assert status_code == 400
        assert "error" in result
        assert "Username already exists" in result["error"]


def test_get_user(app, test_user):
    """
    Test the UserService.get_user method.
    """
    with app.app_context():
        user_id = uuid.UUID(test_user["id"])

        result, status_code = UserService.get_user(user_id)

        assert status_code == 200
        assert result["user_id"] == test_user["id"]
        assert result["username"] == test_user["username"]
        assert result["email"] == test_user["email"]


def test_get_nonexistent_user(app):
    """
    Test the UserService.get_user method with non-existent user.
    """
    with app.app_context():
        nonexistent_user_id = uuid.uuid4()

        result, status_code = UserService.get_user(nonexistent_user_id)

        assert status_code == 404
        assert "error" in result
        assert "User not found" in result["error"]


def test_update_user_self(app, test_user):
    """
    Test the UserService.update_user method for self-update.
    """
    with app.app_context():
        user_id = uuid.UUID(test_user["id"])
        current_user_id = test_user["id"]  # Updating own profile
        new_username = f"updated_{uuid.uuid4().hex[:8]}"
        data = {
            "username": new_username,
            "email": f"{new_username}@example.com",
        }

        result, status_code = UserService.update_user(user_id, current_user_id, data)

        assert status_code == 200
        assert result["username"] == new_username
        assert result["email"] == f"{new_username}@example.com"
        assert result["user_id"] == test_user["id"]


def test_update_user_by_admin(app, test_user, test_admin):
    """
    Test the UserService.update_user method by admin.
    """
    with app.app_context():
        user_id = uuid.UUID(test_user["id"])
        admin_id = test_admin["id"]  # Admin updating another user
        new_username = f"adminupdated_{uuid.uuid4().hex[:8]}"
        data = {
            "username": new_username,
            "email": f"{new_username}@example.com",
            "role": "editor",  # Only admins can change roles
        }

        result, status_code = UserService.update_user(user_id, admin_id, data)

        assert status_code == 200
        assert result["username"] == new_username
        assert result["email"] == f"{new_username}@example.com"
        assert result["role"] == "editor"
        assert result["user_id"] == test_user["id"]


def test_update_user_unauthorized(app, test_user):
    """
    Test the UserService.update_user method with unauthorized access.
    """
    with app.app_context():
        user_id = uuid.UUID(test_user["id"])
        
        # Create another regular user
        other_user = User(
            username=f"other_{uuid.uuid4().hex[:8]}",
            email=f"other_{uuid.uuid4().hex[:8]}@example.com",
            password_hash=generate_password_hash("password123"),
            role="member",
        )
        db.session.add(other_user)
        db.session.commit()
        
        other_user_id = str(other_user.user_id)  # Non-admin trying to update another user
        data = {
            "username": "unauthorized_update",
        }

        result, status_code = UserService.update_user(user_id, other_user_id, data)

        assert status_code == 403
        assert "error" in result
        assert "Unauthorized" in result["error"]


def test_delete_user(app, test_user, test_admin):
    """
    Test the UserService.delete_user method.
    """
    with app.app_context():
        user_id = uuid.UUID(test_user["id"])
        admin_id = test_admin["id"]  # Admin deleting a user

        result, status_code = UserService.delete_user(user_id, admin_id)

        assert status_code == 200
        assert "message" in result
        assert "User deleted successfully" in result["message"]

        # Verify user is actually deleted
        deleted_user = User.query.get(user_id)
        assert deleted_user is None


def test_delete_user_unauthorized(app, test_user):
    """
    Test the UserService.delete_user method with unauthorized access.
    """
    with app.app_context():
        user_id = uuid.UUID(test_user["id"])
        
        # Create another regular user
        other_user = User(
            username=f"other_{uuid.uuid4().hex[:8]}",
            email=f"other_{uuid.uuid4().hex[:8]}@example.com",
            password_hash=generate_password_hash("password123"),
            role="member",
        )
        db.session.add(other_user)
        db.session.commit()
        
        other_user_id = str(other_user.user_id)  # Non-admin trying to delete a user

        result, status_code = UserService.delete_user(user_id, other_user_id)

        assert status_code == 403
        assert "error" in result
        assert "Admin privileges required" in result["error"]


def test_delete_nonexistent_user(app, test_admin):
    """
    Test the UserService.delete_user method with non-existent user.
    """
    with app.app_context():
        nonexistent_user_id = uuid.uuid4()
        admin_id = test_admin["id"]

        result, status_code = UserService.delete_user(nonexistent_user_id, admin_id)

        assert status_code == 404
        assert "error" in result
        assert "User not found" in result["error"]


def test_get_all_users(app, test_user, test_admin):
    """
    Test the UserService.get_all_users method.
    """
    with app.app_context():
        result, status_code = UserService.get_all_users()

        assert status_code == 200
        assert isinstance(result, list)
        assert len(result) >= 2  # At least test_user and test_admin
        assert any(user["username"] == test_user["username"] for user in result)
        assert any(user["username"] == test_admin["username"] for user in result) 