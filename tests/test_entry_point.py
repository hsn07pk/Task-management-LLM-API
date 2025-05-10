import pytest
from flask import json
from sqlalchemy import text

from app import create_app
from blueprints.entry_point import entry_bp
from models import db


@pytest.fixture(scope="module")
def app():
    """Create and configure a Flask app for testing."""
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "postgresql://admin:helloworld123@localhost/task_management_db",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "JWT_SECRET_KEY": "test-secret-key",
        }
    )

    app.register_blueprint(entry_bp)

    with app.app_context():
        db.session.execute(text("DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;"))
        db.session.commit()

        db.create_all()

        yield app

        db.session.remove()
        db.session.execute(text("DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;"))
        db.session.commit()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


def test_api_root(client):
    """Test the API root endpoint returns correct structure and status code."""
    response = client.get("/")
    assert response.status_code == 200

    data = json.loads(response.data)

    assert "name" in data
    assert "version" in data
    assert "_links" in data

    assert data["name"] == "Task Management API"
    assert data["version"] == "1.0"

    links = data["_links"]
    assert "self" in links
    assert "login" in links
    assert "register" in links
    assert "documentation" in links

    assert "href" in links["self"]
    assert "href" in links["login"]
    assert "method" in links["login"]
    assert "templated" in links["login"]
    assert "schema" in links["login"]

    login_schema = links["login"]["schema"]
    assert "type" in login_schema
    assert "properties" in login_schema
    assert "required" in login_schema

    properties = login_schema["properties"]
    assert "email" in properties
    assert "password" in properties

    required_fields = login_schema["required"]
    assert "email" in required_fields
    assert "password" in required_fields


def test_api_root_method_not_allowed(client):
    """Test that POST requests to the API root are not allowed."""
    response = client.post("/")
    assert response.status_code == 405
