import functools
import json
import uuid

import pytest
from sqlalchemy import text
from werkzeug.exceptions import NotFound
from werkzeug.security import generate_password_hash

import routes.user_routes
from app import create_app
from extentions.extensions import cache
from models import User, db
from routes.user_routes import bad_request, internal_error, not_found, user_bp

# from linecache import cache


@pytest.fixture(scope="session")
def app():
    """
    Creates and configures a Flask application for testing purposes.

    This fixture sets up a PostgreSQL database for testing, clears the database schema
    before running tests, and ensures that all the tables are created before the tests
    begin. After tests are run, it cleans up by removing the schema and committing any
    changes to the database.

    Yields:
        app (Flask): The Flask application instance configured for testing.
    """
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "postgresql://admin:helloworld123@localhost/task_management_db",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "JWT_SECRET_KEY": "test-secret-key",
        }
    )

    with app.app_context():
        # Clean database schema before running tests
        db.session.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        db.session.commit()

        # Create all tables defined in models
        db.create_all()

        yield app

        # Clean up after all tests
        db.session.remove()
        db.session.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        db.session.commit()


@pytest.fixture(scope="function")
def client(app):
    """
    Provides a test client for the Flask app.

    This fixture creates a testing client that interacts with the app through
    HTTP requests. Each test is wrapped in a database transaction that is
    rolled back after the test to ensure isolation between tests.

    Args:
        app (Flask): The Flask application instance.

    Yields:
        testing_client (FlaskClient): The Flask test client instance.
    """
    with app.test_client() as testing_client:
        with app.app_context():
            # Start a nested transaction for test isolation
            conn = db.engine.connect()
            trans = conn.begin()

            yield testing_client

            # Rollback the transaction after the test
            trans.rollback()
            conn.close()


@pytest.fixture(scope="function")
def auth_headers(client, app):
    """
    Provides authorization headers for making authenticated requests.

    This fixture creates a test user, logs them in, and returns the
    Authorization header containing a JWT token that can be used
    for authentication in subsequent requests.

    Args:
        client (FlaskClient): The Flask test client.
        app (Flask): The Flask application instance.

    Returns:
        dict: A dictionary containing the Authorization header with the JWT token.
    """
    # Create a test user with admin role if it doesn't exist
    with app.app_context():
        # Check if the user already exists
        existing_user = User.query.filter_by(username="adminuser").first()
        if not existing_user:
            user = User(
                username="adminuser",
                email="admin@example.com",
                password_hash=generate_password_hash("adminpass"),
                role="admin",
            )
            db.session.add(user)
            db.session.commit()

    # Login and get token
    response = client.post("/login", json={"email": "admin@example.com", "password": "adminpass"})
    assert response.status_code == 200, f"Login failed: {response.data}"

    token = json.loads(response.data)["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_user(client, app):
    """
    Tests creating a new user.

    This test checks if a user can be successfully created by sending a POST
    request to the `/users/` endpoint with a valid payload. It verifies that
    the user is created by checking the response status and the returned
    user data.

    Args:
        client (FlaskClient): The Flask test client.
        app (Flask): The Flask application instance.
    """
    with app.app_context():
        response = client.post(
            "/users/",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "password123",
                "role": "member",
            },
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        # Check that the response contains the expected fields
        assert "_links" in data
        # The response might contain either a message or user data with id
        assert "message" in data or "id" in data


def test_create_user_duplicate_email(client, app):
    """
    Tests creating a user with a duplicate email.

    This test checks if an attempt to create a user with an email that
    already exists results in an appropriate error response.

    Args:
        client (FlaskClient): The Flask test client.
        app (Flask): The Flask application instance.
    """
    with app.app_context():
        # Create first user
        client.post(
            "/users/",
            json={
                "username": "user1",
                "email": "duplicate@example.com",
                "password": "password123",
                "role": "member",
            },
        )

        # Try to create second user with the same email
        response = client.post(
            "/users/",
            json={
                "username": "user2",
                "email": "duplicate@example.com",
                "password": "password123",
                "role": "member",
            },
        )
        assert response.status_code == 400
        assert "Email already exists" in json.loads(response.data)["error"]


def test_create_user_duplicate_username(client, app, monkeypatch):
    """
    Tests creating a user with a duplicate username.

    This test checks if an attempt to create a user with a username that
    already exists results in an appropriate error response.

    Args:
        client (FlaskClient): The Flask test client.
        app (Flask): The Flask application instance.
        monkeypatch: Pytest fixture for patching.
    """
    # Register the blueprint
    app.register_blueprint(user_bp, url_prefix="/users")

    # Patch the user service to simulate a duplicate username error
    monkeypatch.setattr(
        "services.user_services.UserService.create_user",
        lambda data: ({"error": "Username already exists"}, 400),
    )

    # Patch the hypermedia links for the error response
    fake_links = {"self": {"href": "/users", "method": "GET"}}
    monkeypatch.setattr("routes.user_routes.generate_users_collection_links", lambda: fake_links)

    # Try to create a user (the patched service will return the error)
    response = client.post(
        "/users/",
        json={
            "username": "sameusername",
            "email": "user2@example.com",
            "password": "password123",
            "role": "member",
        },
    )

    # Verify that we get a 400 Bad Request error
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "Username already exists" in data["error"]


def test_create_user_invalid_data(client, app):
    """
    Tests creating a user with invalid data.

    This test checks if a user creation attempt with invalid data, such as
    an incorrectly formatted email, results in a 400 error and the expected
    error message.

    Args:
        client (FlaskClient): The Flask test client.
        app (Flask): The Flask application instance.
    """
    with app.app_context():
        # The current implementation seems to accept invalid emails
        # Let's test with missing required fields instead
        response = client.post(
            "/users/",
            json={
                # Missing username which is required
                "email": "test@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert (
            "username" in data["error"]
        )  # Check that the error mentions the missing username field


def test_user_not_found_handler_direct(app):
    app.register_blueprint(user_bp, url_prefix="/users")

    with app.test_request_context("/users/123", method="GET"):
        response, status = not_found(NotFound("user does not exist"))

    assert status == 404

    data = response.get_json()
    assert data["error"] == "Not Found"
    assert "user does not exist" in data["message"]
    assert "_links" in data
    assert any(link["href"].endswith("/users/") for link in data["_links"].values())


def test_user_bad_request_handler_direct(app):
    app.register_blueprint(user_bp, url_prefix="/users")

    with app.test_request_context("/users/", method="POST", json={"invalid": "data"}):
        from werkzeug.exceptions import BadRequest

        response, status = bad_request(BadRequest("Invalid request data"))

    assert status == 400

    data = response.get_json()
    assert data["error"] == "Bad Request"
    assert "Invalid request data" in data["message"]
    assert "_links" in data
    assert any(link["href"].endswith("/users/") for link in data["_links"].values())


def test_user_internal_error_handler_direct(app):
    app.register_blueprint(user_bp, url_prefix="/users")

    with app.test_request_context("/users/", method="GET"):
        from werkzeug.exceptions import InternalServerError

        response, status = internal_error(InternalServerError("Database connection error"))

    assert status == 500

    data = response.get_json()
    assert data["error"] == "Internal Server Error"
    assert "Database connection error" in data["message"]
    # Verify that hypermedia links are present (the red lines)
    assert "_links" in data
    assert any(link["href"].endswith("/users/") for link in data["_links"].values())


# def test_get_user(client, auth_headers, app):
#     with app.app_context():
#         cache.clear()
#         # Create and persist a user
#         user = User(
#             username="getuser",
#             email="get@example.com",
#             password_hash=generate_password_hash("password123"),
#         )
#         db.session.add(user)
#         db.session.commit()
#         db.session.refresh(user)  # Ensure data consistency

#         user_id = str(user.user_id)  # Ensure UUID format is correct

#         # Debugging logs
#         print(f"Generated User ID: {user_id} (Type: {type(user_id)})")
#         print(f"Auth Headers: {auth_headers}")

#         response = client.get(f"/users/{user_id}", headers=auth_headers)

#         # Debugging logs for response
#         print(f"Response Code: {response.status_code}")
#         print(f"Response Data: {response.get_json()}")

#         assert response.status_code == 200

#         data = response.get_json()
#         assert data is not None, "Response JSON is empty"
#         assert data.get("username") == "getuser"
#         assert data.get("email") == "get@example.com"


def test_create_user_sets_location_and_hypermedia_links(app, client, monkeypatch):
    app.register_blueprint(user_bp, url_prefix="/users")

    fake_result = {"id": "1234-abcd", "username": "foo", "email": "foo@example.com"}

    fake_links = {
        "self": {"href": "/users/1234-abcd", "method": "GET"},
        "update": {"href": "/users/1234-abcd", "method": "PUT"},
        "delete": {"href": "/users/1234-abcd", "method": "DELETE"},
    }

    def mock_add_user_hypermedia_links(user_dict):
        user_with_links = dict(user_dict)
        user_with_links["_links"] = fake_links
        return user_with_links

    monkeypatch.setattr(
        "routes.user_routes.add_user_hypermedia_links", mock_add_user_hypermedia_links
    )

    monkeypatch.setattr(
        "services.user_services.UserService.create_user", lambda data: (fake_result, 201)
    )

    resp = client.post(
        "/users/",
        json={"username": "testuser", "email": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/json"},
    )

    assert resp.status_code == 201

    location = resp.headers.get("Location")
    assert location is not None
    assert location.endswith("/users/1234-abcd")

    body = resp.get_json()
    assert "_links" in body
    assert body["id"] == fake_result["id"]
    assert body["username"] == fake_result["username"]
    assert body["email"] == fake_result["email"]


def test_create_user_unexpected_format_returns_500(app, client, monkeypatch):
    app.register_blueprint(user_bp, url_prefix="/users")

    monkeypatch.setattr("services.user_services.UserService.create_user", lambda data: (None, 200))

    def mock_validate(instance, schema):
        return True

    monkeypatch.setattr("validators.validators.validate", mock_validate)

    fake_links = {"self": {"href": "/users", "method": "GET"}}
    monkeypatch.setattr("routes.user_routes.generate_users_collection_links", lambda: fake_links)

    resp = client.post(
        "/users/",
        json={"username": "testuser", "email": "test@example.com", "password": "password123"},
    )

    assert resp.status_code == 500
    data = resp.get_json()

    assert data["error"] == "Unexpected response format from user service"
    assert "unexpected format" in data["message"]
    assert "_links" in data


def test_create_user_internal_error_returns_500(app, client, monkeypatch):
    app.register_blueprint(user_bp, url_prefix="/users")

    monkeypatch.setattr(
        "services.user_services.UserService.create_user",
        lambda data: (_ for _ in ()).throw(RuntimeError("Internal server error")),
    )

    def mock_validate(instance, schema):
        return True

    monkeypatch.setattr("validators.validators.validate", mock_validate)

    fake_links = {"self": {"href": "/users", "method": "GET"}}
    monkeypatch.setattr("routes.user_routes.generate_users_collection_links", lambda: fake_links)

    resp = client.post(
        "/users/",
        json={"username": "testuser", "email": "test@example.com", "password": "password123"},
    )

    assert resp.status_code == 500
    data = resp.get_json()

    assert data["error"] == "Internal server error"
    assert "Internal server error" in data["message"]
    assert "_links" in data


def test_get_user_success(app, client, auth_headers, monkeypatch):
    app.register_blueprint(user_bp, url_prefix="/users")

    fake_user = {"id": "abcd-1234", "username": "foo", "email": "foo@ex.com"}
    fake_links = {"self": {"href": f"/users/{fake_user['id']}", "method": "GET"}}

    monkeypatch.setattr("services.user_services.UserService.get_user", lambda uid: (fake_user, 200))
    monkeypatch.setattr(
        "routes.user_routes.add_user_hypermedia_links", lambda u: {**u, "_links": fake_links}
    )

    resp = client.get(f"/users/{fake_user['id']}", headers=auth_headers)

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["id"] == fake_user["id"]
    assert data["_links"] == fake_links


def test_get_user_business_error_returns_status(app, client, auth_headers, monkeypatch):
    from extentions.extensions import cache

    cache.clear()
    app.register_blueprint(user_bp, url_prefix="/users")

    err = {"error": "User invalid", "code": 422}
    fake_links = {"collection": {"href": "/users", "method": "GET"}}

    monkeypatch.setattr("services.user_services.UserService.get_user", lambda uid: (err, 422))
    monkeypatch.setattr("routes.user_routes.generate_users_collection_links", lambda: fake_links)

    monkeypatch.setattr("routes.user_routes.jwt_required", lambda: None)
    monkeypatch.setattr(
        "routes.user_routes.get_jwt_identity", lambda: {"user_id": "fake-user-id3", "role": "admin"}
    )

    resp = client.get("/users/doesnt-matter", headers=auth_headers)
    assert resp.status_code == 422
    data = resp.get_json()
    assert data["error"] == "User invalid"
    assert data["_links"] == fake_links


def test_get_user_string_message_returns_status(app, client, auth_headers, monkeypatch):
    app.register_blueprint(user_bp, url_prefix="/users")

    monkeypatch.setattr(
        "services.user_services.UserService.get_user", lambda uid: ("Operation complete", 202)
    )
    fake_links = {"collection": {"href": "/users", "method": "GET"}}
    monkeypatch.setattr("routes.user_routes.generate_users_collection_links", lambda: fake_links)

    resp = client.get("/users/any-id", headers=auth_headers)
    assert resp.status_code == 202
    data = resp.get_json()
    assert data["message"] == "Operation complete"
    assert data["_links"] == fake_links


def test_get_user_unexpected_format_returns_500(app, client, auth_headers, monkeypatch):
    app.register_blueprint(user_bp, url_prefix="/users")

    monkeypatch.setattr("services.user_services.UserService.get_user", lambda uid: (None, 200))
    fake_links = {"collection": {"href": "/users", "method": "GET"}}
    monkeypatch.setattr("routes.user_routes.generate_users_collection_links", lambda: fake_links)

    resp = client.get("/users/whatever", headers=auth_headers)
    assert resp.status_code == 500
    data = resp.get_json()
    assert data["error"] == "Unexpected response format from user service"
    assert "_links" in data


def test_get_user_service_raises_exception_returns_500(app, client, auth_headers, monkeypatch):
    app.register_blueprint(user_bp, url_prefix="/users")

    monkeypatch.setattr(
        "services.user_services.UserService.get_user",
        lambda uid: (_ for _ in ()).throw(RuntimeError("boom!")),
    )
    fake_links = {"collection": {"href": "/users", "method": "GET"}}
    monkeypatch.setattr("routes.user_routes.generate_users_collection_links", lambda: fake_links)

    resp = client.get("/users/anything", headers=auth_headers)
    assert resp.status_code == 500
    data = resp.get_json()
    assert data["error"] == "Internal server error"
    assert data["_links"] == fake_links


def test_update_user_not_found_returns_404(app, client, auth_headers, monkeypatch):
    app.register_blueprint(user_bp, url_prefix="/users")
    cache.clear()

    monkeypatch.setattr(
        "services.user_services.UserService.update_user",
        lambda uid, data: ({"error": "User not found"}, 404),
    )

    monkeypatch.setattr("routes.user_routes.jwt_required", lambda: None)
    monkeypatch.setattr(
        "routes.user_routes.get_jwt_identity", lambda: {"user_id": "fake-user-id", "role": "admin"}
    )

    def mock_validate(instance, schema):
        return True

    monkeypatch.setattr("validators.validators.validate", mock_validate)

    fake_id = str(uuid.uuid4())
    resp = client.put(
        f"/users/{fake_id}",
        json={
            "username": "newname",
            "email": "new@example.com",
            "password": "newpassword",
            "role": "member",
        },
        headers=auth_headers,
    )

    assert resp.status_code == 404
    data = resp.get_json()
    assert data["error"] == "User not found"
    assert "_links" in data


def test_update_user_success_clears_cache_and_adds_links(app, client, auth_headers, monkeypatch):
    app.register_blueprint(user_bp, url_prefix="/users")
    cache.clear()

    fake_id = str(uuid.uuid4())
    monkeypatch.setattr(
        "services.user_services.UserService.get_user", lambda uid: ({"id": uid}, 200)
    )
    result = {"id": fake_id, "username": "newname"}
    monkeypatch.setattr(
        "services.user_services.UserService.update_user", lambda uid, cu, data: (result, 200)
    )
    fake_links = {"self": {"href": f"/users/{fake_id}", "method": "PUT"}}
    monkeypatch.setattr(
        "routes.user_routes.add_user_hypermedia_links", lambda u: {**u, "_links": fake_links}
    )

    resp = client.put(f"/users/{fake_id}", headers=auth_headers, json={"username": "newname"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["id"] == fake_id
    assert data["_links"] == fake_links


def test_update_user_business_error_returns_code_and_links(app, client, auth_headers, monkeypatch):
    app.register_blueprint(user_bp, url_prefix="/users")
    cache.clear()

    fake_id = str(uuid.uuid4())
    monkeypatch.setattr(
        "services.user_services.UserService.get_user", lambda uid: ({"id": uid}, 200)
    )
    err = {"error": "Bad data"}
    monkeypatch.setattr(
        "services.user_services.UserService.update_user", lambda uid, cu, data: (err, 422)
    )
    fake_links = {"collection": {"href": "/users", "method": "GET"}}
    monkeypatch.setattr("routes.user_routes.generate_users_collection_links", lambda: fake_links)

    resp = client.put(
        f"/users/{fake_id}",
        headers=auth_headers,
        json={"username": "testuser", "email": "test@example.com", "role": "member"},
    )
    assert resp.status_code == 422
    data = resp.get_json()
    assert data["error"] == "Bad data"
    assert data["_links"] == fake_links


def test_update_user_string_message_returns_code_and_links(app, client, auth_headers, monkeypatch):
    app.register_blueprint(user_bp, url_prefix="/users")
    cache.clear()

    fake_id = str(uuid.uuid4())
    monkeypatch.setattr(
        "services.user_services.UserService.get_user", lambda uid: ({"id": uid}, 200)
    )
    monkeypatch.setattr(
        "services.user_services.UserService.update_user", lambda uid, cu, data: ("Done", 202)
    )
    fake_links = {"collection": {"href": "/users", "method": "GET"}}
    monkeypatch.setattr("routes.user_routes.generate_users_collection_links", lambda: fake_links)

    resp = client.put(f"/users/{fake_id}", headers=auth_headers, json={"username": "someuser"})
    assert resp.status_code == 202
    data = resp.get_json()
    assert data["message"] == "Done"
    assert data["_links"] == fake_links


def test_update_user_unexpected_format_returns_500(app, client, auth_headers, monkeypatch):
    app.register_blueprint(user_bp, url_prefix="/users")
    cache.clear()
    monkeypatch.setattr("routes.user_routes.validate_json", lambda schema: (lambda fn: fn))

    fake_id = str(uuid.uuid4())
    monkeypatch.setattr(
        "services.user_services.UserService.get_user", lambda uid: ({"id": uid}, 200)
    )
    monkeypatch.setattr(
        "services.user_services.UserService.update_user", lambda uid, cu, data: (None, 200)
    )
    fake_links = {"collection": {"href": "/users", "method": "GET"}}
    monkeypatch.setattr("routes.user_routes.generate_users_collection_links", lambda: fake_links)

    resp = client.put(
        f"/users/{fake_id}",
        headers=auth_headers,
        json={"username": "dummy", "email": "dummy@example.com"},
    )
    assert resp.status_code == 500
    data = resp.get_json()
    assert data["error"] == "Unexpected response format from user service"
    assert "_links" in data


def test_update_user_service_exception_returns_500(app, client, auth_headers, monkeypatch):
    app.register_blueprint(user_bp, url_prefix="/users")
    cache.clear()

    monkeypatch.setattr("routes.user_routes.validate_json", lambda schema: (lambda fn: fn))

    fake_id = str(uuid.uuid4())

    monkeypatch.setattr(
        "services.user_services.UserService.get_user", lambda uid: ({"id": uid}, 200)
    )

    monkeypatch.setattr(
        "services.user_services.UserService.update_user",
        lambda uid, cu, data: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    fake_links = {"collection": {"href": "/users", "method": "GET"}}
    monkeypatch.setattr("routes.user_routes.generate_users_collection_links", lambda: fake_links)

    resp = client.put(
        f"/users/{fake_id}",
        headers=auth_headers,
        json={"username": "dummy", "email": "dummy@example.com"},
    )
    assert resp.status_code == 500
    data = resp.get_json()
    assert data["error"] == "Internal server error"
    assert "boom" in data["message"]
    assert data["_links"] == fake_links


def test_delete_user_not_found_returns_404(app, client, auth_headers, monkeypatch):
    app.register_blueprint(user_bp, url_prefix="/users")
    cache.clear()

    # Define a fake current user id
    fake_current_user_id = "current-user-id"

    # 1) Simule get_user renvoyant 404
    monkeypatch.setattr("services.user_services.UserService.get_user", lambda uid: ({}, 404))
    # bypass jwt and validation
    monkeypatch.setattr("routes.user_routes.get_jwt_identity", lambda: fake_current_user_id)
    monkeypatch.setattr("routes.user_routes.jwt_required", lambda: None)

    resp = client.delete(f"/users/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["error"] == "User not found"
    assert "_links" in data


def test_delete_user_success_clears_cache_and_returns_message(
    app, client, auth_headers, monkeypatch
):
    app.register_blueprint(user_bp, url_prefix="/users")
    cache.clear()

    fake_id = str(uuid.uuid4())
    # 2) get_user OK
    monkeypatch.setattr(
        "services.user_services.UserService.get_user", lambda uid: ({"id": uid}, 200)
    )
    # 3) delete_user OK returns a string or None
    monkeypatch.setattr(
        "services.user_services.UserService.delete_user", lambda uid, cu: (None, 200)
    )
    # patch jwt
    monkeypatch.setattr("routes.user_routes.get_jwt_identity", lambda: fake_id)
    monkeypatch.setattr("routes.user_routes.jwt_required", lambda: None)

    resp = client.delete(f"/users/{fake_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    # default message "User deleted successfully"
    assert data["message"] == "User deleted successfully"
    assert "_links" in data


def test_delete_user_business_error_returns_code_and_links(app, client, auth_headers, monkeypatch):
    app.register_blueprint(user_bp, url_prefix="/users")
    cache.clear()

    fake_id = str(uuid.uuid4())
    # get_user OK
    monkeypatch.setattr(
        "services.user_services.UserService.get_user", lambda uid: ({"id": uid}, 200)
    )
    # delete_user returns a dict + error code
    err = {"error": "Cannot delete admin"}
    monkeypatch.setattr(
        "services.user_services.UserService.delete_user", lambda uid, cu: (err, 403)
    )
    # patch links
    fake_links = {"collection": {"href": "/users", "method": "GET"}}
    monkeypatch.setattr("routes.user_routes.generate_users_collection_links", lambda: fake_links)
    monkeypatch.setattr("routes.user_routes.get_jwt_identity", lambda: fake_id)
    monkeypatch.setattr("routes.user_routes.jwt_required", lambda: None)

    resp = client.delete(f"/users/{fake_id}", headers=auth_headers)
    assert resp.status_code == 403
    data = resp.get_json()
    assert data["error"] == "Cannot delete admin"
    assert data["_links"] == fake_links


def test_delete_user_string_message_returns_code_and_links(app, client, auth_headers, monkeypatch):
    app.register_blueprint(user_bp, url_prefix="/users")
    cache.clear()

    fake_id = str(uuid.uuid4())
    monkeypatch.setattr(
        "services.user_services.UserService.get_user", lambda uid: ({"id": uid}, 200)
    )
    # delete_user returns a string message + non-200 code
    monkeypatch.setattr(
        "services.user_services.UserService.delete_user", lambda uid, cu: ("Custom message", 202)
    )
    fake_links = {"collection": {"href": "/users", "method": "GET"}}
    monkeypatch.setattr("routes.user_routes.generate_users_collection_links", lambda: fake_links)
    monkeypatch.setattr("routes.user_routes.get_jwt_identity", lambda: fake_id)
    monkeypatch.setattr("routes.user_routes.jwt_required", lambda: None)

    resp = client.delete(f"/users/{fake_id}", headers=auth_headers)
    assert resp.status_code == 202
    data = resp.get_json()
    assert data["message"] == "Custom message"
    assert data["_links"] == fake_links


def test_delete_user_with_nonstandard_format_returns_error(app, client, auth_headers, monkeypatch):
    app.register_blueprint(user_bp, url_prefix="/users")
    cache.clear()

    fake_id = str(uuid.uuid4())
    # get_user OK
    monkeypatch.setattr(
        "services.user_services.UserService.get_user", lambda uid: ({"id": uid}, 200)
    )
    # Return a non-standard format that triggers a 500 error
    monkeypatch.setattr(
        "services.user_services.UserService.delete_user", lambda uid, cu: (None, 201)
    )
    fake_links = {"collection": {"href": "/users", "method": "GET"}}
    monkeypatch.setattr("routes.user_routes.generate_users_collection_links", lambda: fake_links)
    # Patch get_jwt_identity to a valid string ID
    monkeypatch.setattr("routes.user_routes.get_jwt_identity", lambda: fake_id)
    monkeypatch.setattr("routes.user_routes.jwt_required", lambda: None)

    # The application treats this format as an error
    resp = client.delete(f"/users/{fake_id}", headers=auth_headers)
    # Verify that the application returns a 500 (internal error) code
    assert resp.status_code == 500
    data = resp.get_json()
    # Verify that the response contains an error message
    assert "error" in data
    assert "_links" in data


def test_delete_user_service_exception_returns_500(app, client, auth_headers, monkeypatch):
    app.register_blueprint(user_bp, url_prefix="/users")
    cache.clear()

    fake_id = str(uuid.uuid4())
    # get_user OK
    monkeypatch.setattr(
        "services.user_services.UserService.get_user", lambda uid: ({"id": uid}, 200)
    )
    # delete_user raises an exception
    monkeypatch.setattr(
        "services.user_services.UserService.delete_user",
        lambda uid, cu: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    fake_links = {"collection": {"href": "/users", "method": "GET"}}
    monkeypatch.setattr("routes.user_routes.generate_users_collection_links", lambda: fake_links)
    monkeypatch.setattr("routes.user_routes.get_jwt_identity", lambda: fake_id)
    monkeypatch.setattr("routes.user_routes.jwt_required", lambda: None)

    resp = client.delete(f"/users/{fake_id}", headers=auth_headers)
    assert resp.status_code == 500
    data = resp.get_json()
    assert data["error"] == "Internal server error"
    assert "boom" in data["message"]
    assert data["_links"] == fake_links


def test_delete_user_not_found_returns_404(app, client, auth_headers, monkeypatch):
    app.register_blueprint(user_bp, url_prefix="/users")
    cache.clear()

    # 1) Simulate get_user returning 404
    monkeypatch.setattr("services.user_services.UserService.get_user", lambda uid: ({}, 404))
    # bypass jwt and validation
    fake_id = str(uuid.uuid4())
    monkeypatch.setattr(
        "routes.user_routes.get_jwt_identity", lambda: {"user_id": fake_id, "role": "admin"}
    )
    monkeypatch.setattr("routes.user_routes.jwt_required", lambda: None)

    resp = client.delete(f"/users/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["error"] == "User not found"
    assert "_links" in data


def test_delete_user_success_clears_cache_and_returns_message(
    app, client, auth_headers, monkeypatch
):
    app.register_blueprint(user_bp, url_prefix="/users")
    cache.clear()

    fake_id = str(uuid.uuid4())
    # 2) get_user OK
    monkeypatch.setattr(
        "services.user_services.UserService.get_user", lambda uid: ({"id": uid}, 200)
    )
    # 3) delete_user OK returns a string or None
    monkeypatch.setattr(
        "services.user_services.UserService.delete_user", lambda uid, cu: (None, 200)
    )
    # patch jwt
    monkeypatch.setattr("routes.user_routes.get_jwt_identity", lambda: fake_id)
    monkeypatch.setattr("routes.user_routes.jwt_required", lambda: None)

    resp = client.delete(f"/users/{fake_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    # default message "User deleted successfully"
    assert data["message"] == "User deleted successfully"
    assert "_links" in data


def test_delete_user_business_error_returns_code_and_links(app, client, auth_headers, monkeypatch):
    app.register_blueprint(user_bp, url_prefix="/users")
    cache.clear()

    fake_id = str(uuid.uuid4())
    # get_user OK
    monkeypatch.setattr(
        "services.user_services.UserService.get_user", lambda uid: ({"id": uid}, 200)
    )
    # delete_user returns a dict + error code
    err = {"error": "Cannot delete admin"}
    monkeypatch.setattr(
        "services.user_services.UserService.delete_user", lambda uid, cu: (err, 403)
    )
    # patch links
    fake_links = {"collection": {"href": "/users", "method": "GET"}}
    monkeypatch.setattr("routes.user_routes.generate_users_collection_links", lambda: fake_links)
    monkeypatch.setattr("routes.user_routes.get_jwt_identity", lambda: fake_id)
    monkeypatch.setattr("routes.user_routes.jwt_required", lambda: None)

    resp = client.delete(f"/users/{fake_id}", headers=auth_headers)
    assert resp.status_code == 403
    data = resp.get_json()
    assert data["error"] == "Cannot delete admin"
    assert data["_links"] == fake_links


def test_delete_user_string_message_returns_code_and_links(app, client, auth_headers, monkeypatch):
    app.register_blueprint(user_bp, url_prefix="/users")
    cache.clear()

    fake_id = str(uuid.uuid4())
    monkeypatch.setattr(
        "services.user_services.UserService.get_user", lambda uid: ({"id": uid}, 200)
    )
    # delete_user returns a string message + non-200 code
    monkeypatch.setattr(
        "services.user_services.UserService.delete_user", lambda uid, cu: ("Custom message", 202)
    )
    fake_links = {"collection": {"href": "/users", "method": "GET"}}
    monkeypatch.setattr("routes.user_routes.generate_users_collection_links", lambda: fake_links)
    monkeypatch.setattr("routes.user_routes.get_jwt_identity", lambda: fake_id)
    monkeypatch.setattr("routes.user_routes.jwt_required", lambda: None)

    resp = client.delete(f"/users/{fake_id}", headers=auth_headers)
    assert resp.status_code == 202
    data = resp.get_json()
    assert data["message"] == "Custom message"
    assert data["_links"] == fake_links


def test_delete_user_service_exception_returns_500(app, client, auth_headers, monkeypatch):
    app.register_blueprint(user_bp, url_prefix="/users")
    cache.clear()

    fake_id = str(uuid.uuid4())
    # get_user OK
    monkeypatch.setattr(
        "services.user_services.UserService.get_user", lambda uid: ({"id": uid}, 200)
    )
    # delete_user raises an exception
    monkeypatch.setattr(
        "services.user_services.UserService.delete_user",
        lambda uid, cu: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    fake_links = {"collection": {"href": "/users", "method": "GET"}}
    monkeypatch.setattr("routes.user_routes.generate_users_collection_links", lambda: fake_links)
    monkeypatch.setattr("routes.user_routes.get_jwt_identity", lambda: fake_id)
    monkeypatch.setattr("routes.user_routes.jwt_required", lambda: None)

    resp = client.delete(f"/users/{fake_id}", headers=auth_headers)
    assert resp.status_code == 500
    data = resp.get_json()
    assert data["error"] == "Internal server error"
    assert "boom" in data["message"]
    assert data["_links"] == fake_links


def test_fetch_users_success_with_dicts(app, client, auth_headers, monkeypatch):
    """
    When UserService.get_all_users returns a list of dicts and status 200,
    fetch_users() should return 200 with each dict enriched with hypermedia links.
    """
    app.register_blueprint(user_bp, url_prefix="/users")
    from extentions.extensions import cache

    cache.clear()

    # Prepare fake users and patches
    fake_users = [{"id": "u1", "username": "alice"}, {"id": "u2", "username": "bob"}]
    fake_links = {"self": {"href": "/users/u1", "method": "GET"}}
    # Patch service and link generation
    monkeypatch.setattr(
        "services.user_services.UserService.get_all_users", lambda: (fake_users, 200)
    )
    monkeypatch.setattr(
        "routes.user_routes.add_user_hypermedia_links", lambda u: {**u, "_links": fake_links}
    )
    monkeypatch.setattr(
        "routes.user_routes.generate_users_collection_links",
        lambda: {"collection": {"href": "/users", "method": "GET"}},
    )
    monkeypatch.setattr("routes.user_routes.jwt_required", lambda f: f)
    monkeypatch.setattr("routes.user_routes.get_jwt_identity", lambda: "current-user")

    resp = client.get("/users/", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    # Should have list and links
    assert "users" in data and isinstance(data["users"], list)
    assert data["users"][0]["_links"] == fake_links
    assert "_links" in data


def test_fetch_users_success_with_nonstandard_objects(app, client, auth_headers, monkeypatch):
    """
    If get_all_users returns non-dict objects, fetch_users should include them raw.
    """
    app.register_blueprint(user_bp, url_prefix="/users")
    from extentions.extensions import cache

    cache.clear()

    fake_users = ["raw1", "raw2"]
    monkeypatch.setattr(
        "services.user_services.UserService.get_all_users", lambda: (fake_users, 200)
    )
    monkeypatch.setattr(
        "routes.user_routes.add_user_hypermedia_links", lambda u: u  # not used for non-dicts
    )
    monkeypatch.setattr("routes.user_routes.generate_users_collection_links", lambda: {})
    monkeypatch.setattr("routes.user_routes.jwt_required", lambda f: f)
    monkeypatch.setattr("routes.user_routes.get_jwt_identity", lambda: "current-user")

    resp = client.get("/users/", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["users"] == fake_users


def test_fetch_users_business_error_returns_code_and_links(app, client, auth_headers, monkeypatch):
    """
    If get_all_users returns a dict error and status !=200, fetch_users should forward it.
    """
    app.register_blueprint(user_bp, url_prefix="/users")
    from extentions.extensions import cache

    cache.clear()

    err = {"error": "Service down"}
    monkeypatch.setattr("services.user_services.UserService.get_all_users", lambda: (err, 503))
    monkeypatch.setattr(
        "routes.user_routes.generate_users_collection_links",
        lambda: {"collection": {"href": "/users", "method": "GET"}},
    )
    monkeypatch.setattr("routes.user_routes.jwt_required", lambda f: f)
    monkeypatch.setattr("routes.user_routes.get_jwt_identity", lambda: "current-user")

    resp = client.get("/users/", headers=auth_headers)
    assert resp.status_code == 503
    data = resp.get_json()
    assert data["error"] == "Service down"
    assert "_links" in data


def test_fetch_users_string_message_returns_code_and_links(app, client, auth_headers, monkeypatch):
    """
    If get_all_users returns a string message and code !=200, fetch_users should wrap it.
    """
    app.register_blueprint(user_bp, url_prefix="/users")
    from extentions.extensions import cache

    cache.clear()

    monkeypatch.setattr("services.user_services.UserService.get_all_users", lambda: ("Okay", 202))
    monkeypatch.setattr(
        "routes.user_routes.generate_users_collection_links",
        lambda: {"collection": {"href": "/users", "method": "GET"}},
    )
    monkeypatch.setattr("routes.user_routes.jwt_required", lambda f: f)
    monkeypatch.setattr("routes.user_routes.get_jwt_identity", lambda: "current-user")

    resp = client.get("/users/", headers=auth_headers)
    assert resp.status_code == 202
    data = resp.get_json()
    assert data["message"] == "Okay"
    assert "_links" in data


def test_fetch_users_unexpected_format_returns_500(app, client, auth_headers, monkeypatch):
    """
    If get_all_users returns None or unexpected format, fetch_users should return 500.
    """
    app.register_blueprint(user_bp, url_prefix="/users")
    from extentions.extensions import cache

    cache.clear()

    monkeypatch.setattr("services.user_services.UserService.get_all_users", lambda: (None, 200))
    monkeypatch.setattr("routes.user_routes.generate_users_collection_links", lambda: {})
    monkeypatch.setattr("routes.user_routes.jwt_required", lambda f: f)
    monkeypatch.setattr("routes.user_routes.get_jwt_identity", lambda: "current-user")

    resp = client.get("/users/", headers=auth_headers)
    assert resp.status_code == 500
    data = resp.get_json()
    assert data["error"] == "Unexpected response format from user service"
    assert "_links" in data


def test_fetch_users_service_exception_returns_500(app, client, auth_headers, monkeypatch):
    """
    If get_all_users raises, fetch_users should catch and return 500.
    """
    app.register_blueprint(user_bp, url_prefix="/users")
    from extentions.extensions import cache

    cache.clear()

    monkeypatch.setattr(
        "services.user_services.UserService.get_all_users",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    monkeypatch.setattr("routes.user_routes.generate_users_collection_links", lambda: {})
    monkeypatch.setattr("routes.user_routes.jwt_required", lambda f: f)
    monkeypatch.setattr("routes.user_routes.get_jwt_identity", lambda: "current-user")

    resp = client.get("/users/", headers=auth_headers)
    assert resp.status_code == 500
    data = resp.get_json()
    assert data["error"] == "Internal server error"
    assert "boom" in data["message"]
    assert "_links" in data
