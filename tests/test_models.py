import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import text
from werkzeug.security import check_password_hash, generate_password_hash

from models import (PriorityEnum, Project, StatusEnum, Task, Team,
                    TeamMembership, User, assign_task, create_task,
                    create_team, create_user, db, delete_task, delete_user,
                    get_all_users, get_project_tasks, get_task, get_user_by_id,
                    update_user)


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


@pytest.fixture(scope="session")
def _db(app):
    """
    Set up the database before running tests.
    """
    with app.app_context():
        # Clean database schema before running tests
        db.session.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        db.session.commit()

        # Create all tables
        db.create_all()

        yield db

        # Clean up after all tests
        db.session.remove()
        db.session.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        db.session.commit()


@pytest.fixture(scope="function")
def app_for_exception_tests():
    """
    Configure a Flask app for testing with SQLite in-memory database.
    """
    from app import create_app

    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "JWT_SECRET_KEY": "test-secret-key",
        }
    )

    return app


@pytest.fixture(scope="function")
def db_for_exception_tests(app_for_exception_tests):
    """
    Set up an in-memory database for exception testing.
    """
    with app_for_exception_tests.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


def test_user_model_to_dict(app, _db):
    """
    Test the to_dict method of the User model.
    """
    with app.app_context():
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=generate_password_hash("password123"),
            role="member",
        )
        db.session.add(user)
        db.session.commit()

        user_dict = user.to_dict()
        assert user_dict["username"] == "testuser"
        assert user_dict["email"] == "test@example.com"
        assert user_dict["role"] == "member"
        assert "user_id" in user_dict
        assert "_links" in user_dict


def test_team_model_to_dict(app, _db):
    """
    Test the to_dict method of the Team model.
    """
    with app.app_context():
        user = User(
            username="teamlead",
            email="lead@example.com",
            password_hash=generate_password_hash("password123"),
            role="member",
        )
        db.session.add(user)
        db.session.commit()

        team = Team(
            name="Test Team",
            description="A team for testing",
            lead_id=user.user_id,
        )
        db.session.add(team)
        db.session.commit()

        team_dict = team.to_dict()
        assert team_dict["name"] == "Test Team"
        assert team_dict["description"] == "A team for testing"
        assert team_dict["lead_id"] == str(user.user_id)
        assert "team_id" in team_dict
        assert "_links" in team_dict


def test_project_model_to_dict(app, _db):
    """
    Test the to_dict method of the Project model.
    """
    with app.app_context():
        # Create a team first
        user = User(
            username="projectlead",
            email="plead@example.com",
            password_hash=generate_password_hash("password123"),
        )
        db.session.add(user)
        db.session.commit()

        team = Team(name="Project Team", lead_id=user.user_id)
        db.session.add(team)
        db.session.commit()

        # Create a project
        project = Project(
            title="Test Project",
            description="A project for testing",
            status="planning",
            deadline=datetime.utcnow() + timedelta(days=30),
            team_id=team.team_id,
        )
        db.session.add(project)
        db.session.commit()

        project_dict = project.to_dict()
        assert project_dict["title"] == "Test Project"
        assert project_dict["description"] == "A project for testing"
        assert project_dict["status"] == "planning"
        assert "project_id" in project_dict
        assert "deadline" in project_dict
        assert project_dict["team_id"] == str(team.team_id)
        assert "_links" in project_dict


def test_task_model_to_dict(app, _db):
    """
    Test the to_dict method of the Task model.
    """
    with app.app_context():
        # Create a user
        user = User(
            username="taskuser",
            email="task@example.com",
            password_hash=generate_password_hash("password123"),
        )
        db.session.add(user)
        db.session.commit()

        # Create a project
        project = Project(
            title="Task Project",
            description="A project with tasks",
            status="active",
        )
        db.session.add(project)
        db.session.commit()

        # Create a task
        task = Task(
            title="Test Task",
            description="A task for testing",
            priority=PriorityEnum.MEDIUM.value,
            status=StatusEnum.PENDING.value,
            deadline=datetime.utcnow() + timedelta(days=7),
            project_id=project.project_id,
            assignee_id=user.user_id,
            created_by=user.user_id,
            updated_by=user.user_id,
        )
        db.session.add(task)
        db.session.commit()

        task_dict = task.to_dict()
        assert task_dict["title"] == "Test Task"
        assert task_dict["description"] == "A task for testing"
        assert task_dict["priority"] == PriorityEnum.MEDIUM.value
        assert task_dict["status"] == StatusEnum.PENDING.value
        assert "task_id" in task_dict
        assert "deadline" in task_dict
        assert task_dict["project_id"] == str(project.project_id)
        assert task_dict["assignee_id"] == str(user.user_id)
        assert "_links" in task_dict


def test_create_user_function(app, _db):
    """
    Test the create_user function.
    """
    with app.app_context():
        user = create_user(
            username="functionuser",
            email="function@example.com",
            password="securepass",
            role="member",
        )

        assert user is not None
        assert user.username == "functionuser"
        assert user.email == "function@example.com"
        assert user.role == "member"
        assert check_password_hash(user.password_hash, "securepass")

        # Test duplicate user handling
        with pytest.raises(ValueError, match="Username or email already exists"):
            create_user(
                username="functionuser",
                email="new@example.com",
                password="password",
            )


def test_get_user_by_id_function(app, _db):
    """
    Test the get_user_by_id function.
    """
    with app.app_context():
        # Create a user first
        user = create_user(
            username="getuser",
            email="get@example.com",
            password="password123",
        )

        # Test getting the user by ID
        retrieved_user = get_user_by_id(user.user_id)
        assert retrieved_user is not None
        assert retrieved_user.username == "getuser"
        assert retrieved_user.email == "get@example.com"

        # Test with non-existent ID
        non_existent_id = uuid.uuid4()
        assert get_user_by_id(non_existent_id) is None


def test_update_user_function(app, _db):
    """
    Test the update_user function.
    """
    with app.app_context():
        # Create a user first
        user = create_user(
            username="updateuser",
            email="update@example.com",
            password="password123",
        )

        # Update the user
        updated_user = update_user(
            user.user_id,
            username="newusername",
            email="newemail@example.com",
            role="admin",
        )

        assert updated_user is not None
        assert updated_user.username == "newusername"
        assert updated_user.email == "newemail@example.com"
        assert updated_user.role == "admin"

        # Test with non-existent ID
        non_existent_id = uuid.uuid4()
        with pytest.raises(RuntimeError) as excinfo:
            update_user(non_existent_id, username="nonexistent")
        # Verify that the error message contains the ID and a mention of "not found"
        error_msg = str(excinfo.value)
        assert "Error updating user" in error_msg
        assert str(non_existent_id) in error_msg
        assert "not found" in error_msg


def test_delete_user_function(app, _db):
    """
    Test the delete_user function.
    """
    with app.app_context():
        # Create a user first
        user = create_user(
            username="deleteuser",
            email="delete@example.com",
            password="password123",
        )

        # Delete the user
        result = delete_user(user.user_id)
        assert result is not None  # Check that the user object is returned
        assert result.user_id == user.user_id  # Check that it's the correct user

        # Verify the user is deleted
        assert get_user_by_id(user.user_id) is None

        # Test with non-existent ID
        non_existent_id = uuid.uuid4()
        result = delete_user(non_existent_id)
        assert result is None  # Pour un ID non existant, la fonction retourne None


def test_get_all_users_function(app, _db):
    """
    Test the get_all_users function.
    """
    with app.app_context():
        # Create multiple users
        create_user(username="user1", email="user1@example.com", password="password1")
        create_user(username="user2", email="user2@example.com", password="password2")
        create_user(username="user3", email="user3@example.com", password="password3")

        # Get all users
        users = get_all_users()
        assert users is not None
        assert len(users) >= 3
        assert any(user.username == "user1" for user in users)
        assert any(user.username == "user2" for user in users)
        assert any(user.username == "user3" for user in users)


def test_create_team_function(app, _db):
    """
    Test the create_team function.
    """
    with app.app_context():
        # Create a user first to be the lead
        user = create_user(
            username="teamcreator",
            email="teamcreator@example.com",
            password="password123",
        )

        # Create a team
        team = create_team(
            name="Function Team",
            description="A team created by function",
            lead_id=user.user_id,
        )

        assert team is not None
        assert team.name == "Function Team"
        assert team.description == "A team created by function"
        assert team.lead_id == user.user_id


def test_create_and_get_task_functions(app, _db):
    """
    Test the create_task and get_task functions.
    """
    with app.app_context():
        # Create a user
        user = create_user(
            username="taskowner",
            email="taskowner@example.com",
            password="password123",
        )

        # Create a project
        project = Project(
            title="Task Function Project",
            description="For testing task functions",
            status="active",
        )
        db.session.add(project)
        db.session.commit()

        # Create a task
        task = create_task(
            title="Function Task",
            description="Created by function",
            priority=PriorityEnum.HIGH.value,
            deadline=datetime.utcnow() + timedelta(days=5),
            status=StatusEnum.PENDING.value,
            project_id=project.project_id,
            assignee_id=user.user_id,
            created_by=user.user_id,
            updated_by=user.user_id,
        )

        assert task is not None
        assert task.title == "Function Task"
        assert task.description == "Created by function"
        assert task.priority == PriorityEnum.HIGH.value
        assert task.status == StatusEnum.PENDING.value
        assert task.project_id == project.project_id
        assert task.assignee_id == user.user_id

        # Test get_task function
        retrieved_task = get_task(task.task_id)
        assert retrieved_task is not None
        assert retrieved_task.task_id == task.task_id
        assert retrieved_task.title == "Function Task"

        # Test get_project_tasks function
        project_tasks = get_project_tasks(project.project_id)
        assert project_tasks is not None
        assert len(project_tasks) >= 1
        assert any(t.title == "Function Task" for t in project_tasks)


def test_assign_task_function(app, _db):
    """
    Test the assign_task function.
    """
    with app.app_context():
        # Create users
        creator = create_user(
            username="taskcreator",
            email="creator@example.com",
            password="password123",
        )
        assignee = create_user(
            username="assignee",
            email="assignee@example.com",
            password="password123",
        )

        # Create a project
        project = Project(
            title="Assignment Project",
            description="For testing task assignment",
            status="active",
        )
        db.session.add(project)
        db.session.commit()

        # Assign a task
        task = assign_task(
            title="Assigned Task",
            description="Task to be assigned",
            priority=PriorityEnum.MEDIUM.value,
            project_id=project.project_id,
            assignee_id=assignee.user_id,
            created_by=creator.user_id,
        )

        assert task is not None
        assert task.title == "Assigned Task"
        assert task.description == "Task to be assigned"
        assert task.priority == PriorityEnum.MEDIUM.value
        assert task.project_id == project.project_id
        assert task.assignee_id == assignee.user_id
        assert task.created_by == creator.user_id


def test_delete_task_function(app, _db):
    """
    Test the delete_task function.
    """
    with app.app_context():
        # Create a user
        user = create_user(
            username="deletetaskuser",
            email="deletetask@example.com",
            password="password123",
        )

        # Create a project
        project = Project(
            title="Delete Task Project",
            description="For testing task deletion",
            status="active",
        )
        db.session.add(project)
        db.session.commit()

        # Create a task
        task = create_task(
            title="Task to Delete",
            description="This task will be deleted",
            project_id=project.project_id,
            created_by=user.user_id,
        )

        # Delete the task
        result = delete_task(task.task_id)
        assert result is True

        # Verify the task is deleted
        assert get_task(task.task_id) is None

        # Test with non-existent ID
        non_existent_id = uuid.uuid4()
        assert delete_task(non_existent_id) is False  # Should return False, not raise an exception


def test_team_membership_model(app, _db):
    """
    Test the TeamMembership model.
    """
    with app.app_context():
        # Create a user
        user = create_user(
            username="memberuser",
            email="member@example.com",
            password="password123",
        )

        # Create a team
        team = create_team(
            name="Membership Team",
            description="Team for testing membership",
            lead_id=user.user_id,
        )

        # Create a membership
        membership = TeamMembership(
            user_id=user.user_id,
            team_id=team.team_id,
            role="admin",
        )
        db.session.add(membership)
        db.session.commit()

        # Fetch the membership
        stored_membership = TeamMembership.query.filter_by(
            user_id=user.user_id, team_id=team.team_id
        ).first()
        assert stored_membership is not None
        assert stored_membership.role == "admin"


def test_priority_and_status_enums():
    """
    Test the PriorityEnum and StatusEnum.
    """
    # Test PriorityEnum values
    assert PriorityEnum.HIGH.value == 1
    assert PriorityEnum.MEDIUM.value == 2
    assert PriorityEnum.LOW.value == 3

    # Test StatusEnum values
    assert StatusEnum.PENDING.value == "pending"
    assert StatusEnum.IN_PROGRESS.value == "in_progress"
    assert StatusEnum.COMPLETED.value == "completed"


def test_priority_enum_string_conversion(app, _db):
    """
    Test that a string priority value is correctly converted to its integer equivalent in the TaskService.
    """
    with app.app_context():
        # Test the enumeration values directly
        assert PriorityEnum.HIGH.value == 1
        assert PriorityEnum.MEDIUM.value == 2
        assert PriorityEnum.LOW.value == 3
        
        # Create a user, project and task to test TaskService
        user = User(
            username="task_service_tester",
            email="taskservice@example.com",
            password_hash=generate_password_hash("password123")
        )
        db.session.add(user)
        
        project = Project(
            title="TaskService Test Project",
            description="Testing priority conversion"
        )
        db.session.add(project)
        db.session.commit()
        
        # Data with a string priority
        task_data = {
            "title": "String Priority Task",
            "description": "Task with string priority",
            "priority": "HIGH",
            "project_id": str(project.project_id)
        }
        
        # Use TaskService.create_task which handles the conversion
        from services.task_service import TaskService
        task_dict = TaskService.create_task(task_data, str(user.user_id))
        
        # Verify that the priority has been correctly converted to an integer
        assert task_dict["priority"] == PriorityEnum.HIGH.value
        
        # Test with task update
        task = Task(
            title="Task to update",
            description="Initial description",
            priority=PriorityEnum.LOW.value,
            project_id=project.project_id,
            created_by=user.user_id
        )
        db.session.add(task)
        db.session.commit()
        
        # Update with a string priority
        update_data = {
            "priority": "MEDIUM"  # String value
        }
        
        updated_task = TaskService.update_task(task.task_id, update_data, str(user.user_id))
        assert updated_task["priority"] == PriorityEnum.MEDIUM.value


def test_task_model_default_values(app, _db):
    """
    Test that default values are correctly set in the Task model.
    """
    with app.app_context():
        # Create a task with minimal parameters
        task = Task(title="Default Values Test")
        db.session.add(task)
        db.session.commit()
        
        # Check default values
        assert task.status == StatusEnum.PENDING.value
        assert task.priority == PriorityEnum.LOW.value
        assert task.description is None
        assert task.deadline is None
        assert task.project_id is None
        assert task.assignee_id is None
        assert task.created_by is None
        assert task.updated_by is None


def test_task_model_relationships(app, _db):
    """
    Test the relationships between Task and other models.
    """
    with app.app_context():
        # Create user
        user = User(
            username="relationship_tester",
            email="relationships@example.com",
            password_hash=generate_password_hash("password123")
        )
        db.session.add(user)
        
        # Create project
        project = Project(
            title="Relationship Test Project",
            description="Testing relationships"
        )
        db.session.add(project)
        db.session.commit()
        
        # Create task with relationships
        task = Task(
            title="Relationship Test Task",
            project_id=project.project_id,
            assignee_id=user.user_id,
            created_by=user.user_id,
            updated_by=user.user_id
        )
        db.session.add(task)
        db.session.commit()
        
        # Test relationship from task
        assert task.project.title == "Relationship Test Project"
        assert task.assignee.username == "relationship_tester"
        
        # Test reverse relationship from project to tasks
        assert len(project.tasks) == 1
        assert project.tasks[0].title == "Relationship Test Task"
        
        # Test reverse relationship from user to tasks
        assert len(user.tasks) >= 1
        assert any(t.title == "Relationship Test Task" for t in user.tasks)


def test_cascade_delete_project_tasks(app, _db):
    """
    Test that deleting a project also deletes its associated tasks (cascade).
    """
    with app.app_context():
        # Create project
        project = Project(
            title="Cascade Delete Test",
            description="Testing cascade delete"
        )
        db.session.add(project)
        db.session.commit()
        
        # Create tasks for the project
        task1 = Task(
            title="Cascade Task 1",
            project_id=project.project_id
        )
        task2 = Task(
            title="Cascade Task 2",
            project_id=project.project_id
        )
        db.session.add_all([task1, task2])
        db.session.commit()
        
        # Store task IDs for later verification
        task1_id = task1.task_id
        task2_id = task2.task_id
        
        # Delete the project
        db.session.delete(project)
        db.session.commit()
        
        # Verify tasks are also deleted
        assert Task.query.get(task1_id) is None
        assert Task.query.get(task2_id) is None


def test_user_model_password_hashing(app, _db):
    """
    Test password hashing in User model and create_user function.
    """
    with app.app_context():
        # Test with create_user function
        password = "secure_password123"
        user = create_user(
            username="password_test_user",
            email="password@example.com",
            password=password
        )
        
        # Verify password is hashed and not stored in plaintext
        assert user.password_hash != password
        assert check_password_hash(user.password_hash, password)
        
        # Manual user creation
        manual_user = User(
            username="manual_pass_user",
            email="manual_pass@example.com",
            password_hash=generate_password_hash("manual_password")
        )
        db.session.add(manual_user)
        db.session.commit()
        
        assert check_password_hash(manual_user.password_hash, "manual_password")
        assert not check_password_hash(manual_user.password_hash, "wrong_password")


def test_team_membership_roles(app, _db):
    """
    Test different roles in TeamMembership.
    """
    with app.app_context():
        # Create user and team
        user = User(
            username="membership_tester",
            email="membership@example.com",
            password_hash=generate_password_hash("password123")
        )
        team = Team(
            name="Membership Test Team",
            description="Testing team memberships with different roles"
        )
        db.session.add_all([user, team])
        db.session.commit()
        
        # Create memberships with different roles
        roles = ["member", "admin", "viewer", "contributor"]
        memberships = []
        
        for i, role in enumerate(roles):
            # Create additional users for different roles
            if i > 0:
                user = User(
                    username=f"membership_tester_{i}",
                    email=f"membership{i}@example.com",
                    password_hash=generate_password_hash("password123")
                )
                db.session.add(user)
                db.session.commit()
            
            membership = TeamMembership(
                user_id=user.user_id,
                team_id=team.team_id,
                role=role
            )
            db.session.add(membership)
            memberships.append((user.user_id, role))
        
        db.session.commit()
        
        # Verify roles were stored correctly
        for user_id, expected_role in memberships:
            stored_membership = TeamMembership.query.filter_by(
                user_id=user_id, team_id=team.team_id
            ).first()
            assert stored_membership is not None
            assert stored_membership.role == expected_role


def test_model_validation_constraints(app, _db):
    """
    Test database constraints and validation in models.
    """
    with app.app_context():
        # Test User model constraints (unique username/email)
        user1 = User(
            username="unique_constraint_test",
            email="unique@example.com",
            password_hash=generate_password_hash("password123")
        )
        db.session.add(user1)
        db.session.commit()
        
        # Try to create a user with the same username
        user2 = User(
            username="unique_constraint_test",
            email="different@example.com",
            password_hash=generate_password_hash("password123")
        )
        db.session.add(user2)
        
        # Should fail with IntegrityError
        with pytest.raises(Exception): 
            db.session.commit()
        
        db.session.rollback()
        
        # Test not-null constraints
        with pytest.raises(Exception):
            # Task title is required (not nullable)
            task = Task(description="Missing required title")
            db.session.add(task)
            db.session.commit()
            
        db.session.rollback()


def test_exception_in_init_db(mocker):
    """
    Test exception handling in init_db function.
    """
    from models import init_db
    from app import create_app
    
    app = create_app()
    
    # Mock db.init_app to raise an exception
    mock_init_app = mocker.patch('models.db.init_app', side_effect=Exception("Database connection error"))
    
    # Call init_db and verify it returns False on exception
    result = init_db(app)
    assert result is False
    mock_init_app.assert_called_once_with(app)


def test_get_user_by_id_invalid_uuid_format():
    """
    Test get_user_by_id with an invalid UUID format without using a database.
    """
    # Test with invalid UUID format
    invalid_id = "not-a-uuid"
    result = get_user_by_id(invalid_id)
    assert result is None
    
    # Test with an object that raises TypeError
    class NonStringObject:
        def __str__(self):
            raise TypeError("Cannot convert to string")
    
    invalid_obj = NonStringObject()
    result = get_user_by_id(invalid_obj)
    assert result is None


def test_get_task_invalid_uuid_format():
    """
    Test get_task with an invalid UUID format without using a database.
    """
    # Test with invalid UUID format
    invalid_id = "not-a-uuid"
    result = get_task(invalid_id)
    assert result is None
    
    # Test with an object that raises TypeError
    class NonStringObject:
        def __str__(self):
            raise TypeError("Cannot convert to string")
    
    invalid_obj = NonStringObject()
    result = get_task(invalid_obj)
    assert result is None


def test_delete_task_invalid_uuid_format(app):
    """
    Test delete_task with an invalid UUID format without using a database.
    """
    with app.app_context():
        # Test with invalid UUID format
        invalid_id = "not-a-uuid"
        result = delete_task(invalid_id)
        assert result is False
        
        # Test with an object that raises TypeError
        class NonStringObject:
            def __str__(self):
                raise TypeError("Cannot convert to string")
        
        invalid_obj = NonStringObject()
        result = delete_task(invalid_obj)
        assert result is False


def test_create_task_invalid_uuid_formats(app):
    """
    Test create_task with invalid UUID formats without using a database.
    """
    with app.app_context():
        # Test with invalid project_id
        with pytest.raises(RuntimeError) as exc_info:
            create_task(
                title="Test Task",
                description="Test Description",
                project_id="not-a-uuid",
            )
        assert "Invalid project ID format" in str(exc_info.value)
        
        # Test with invalid assignee_id
        with pytest.raises(RuntimeError) as exc_info:
            create_task(
                title="Test Task",
                description="Test Description",
                assignee_id="not-a-uuid",
            )
        assert "Invalid assignee ID format" in str(exc_info.value)
        
        # Test with invalid created_by
        with pytest.raises(RuntimeError) as exc_info:
            create_task(
                title="Test Task",
                description="Test Description",
                created_by="not-a-uuid",
            )
        assert "Invalid creator ID format" in str(exc_info.value)
        
        # Test with invalid updated_by
        with pytest.raises(RuntimeError) as exc_info:
            create_task(
                title="Test Task",
                description="Test Description",
                updated_by="not-a-uuid",
            )
        assert "Invalid updater ID format" in str(exc_info.value)


def test_create_task_database_exception(app, mocker):
    """
    Test database exception handling in create_task using mocks.
    """
    with app.app_context():
        # Mock db.session.add to raise an exception
        mocker.patch('models.db.session.add', side_effect=Exception("Database error"))
        
        with pytest.raises(RuntimeError) as exc_info:
            create_task(
                title="Test Task",
                description="Test Description",
            )
        assert "Error creating task" in str(exc_info.value)


def test_create_team_database_exception(app, mocker):
    """
    Test database exception handling in create_team using mocks.
    """
    with app.app_context():
        # Mock db.session.add to raise an exception
        mocker.patch('models.db.session.add', side_effect=Exception("Database error"))
        
        with pytest.raises(RuntimeError) as exc_info:
            create_team(
                name="Test Team",
                description="Test Description",
                lead_id=None,
            )
        assert "Error creating team" in str(exc_info.value)


def test_assign_task_invalid_priority(app):
    """
    Test assign_task with invalid priority format without using a database.
    """
    with app.app_context():
        # Test with invalid priority type
        with pytest.raises(RuntimeError) as exc_info:
            assign_task(
                title="Test Task",
                description="Test Description",
                priority="invalid_priority",
                project_id=None,
                assignee_id=None,
            )
        assert "Priority must be a valid integer" in str(exc_info.value)
        
        # Test with out-of-range priority
        with pytest.raises(RuntimeError) as exc_info:
            assign_task(
                title="Test Task",
                description="Test Description",
                priority=99,
                project_id=None,
                assignee_id=None,
            )
        assert "Priority must be a valid integer" in str(exc_info.value)


def test_delete_user_database_exception(app, mocker):
    """
    Test database exception handling in delete_user using mocks.
    """
    with app.app_context():
        # Create a mock user with an ID
        mock_user = mocker.MagicMock()
        mock_user.user_id = uuid.uuid4()
        
        # Mock get_user_by_id to return our mock user
        mocker.patch('models.get_user_by_id', return_value=mock_user)
        
        # Mock db.session.delete to raise an exception
        mocker.patch('models.db.session.delete', side_effect=Exception("Database error"))
        
        with pytest.raises(RuntimeError) as exc_info:
            delete_user(mock_user.user_id)
        assert "Error deleting user" in str(exc_info.value)


def test_get_all_users_exception(app, mocker):
    """
    Test exception handling in get_all_users using mocks.
    """
    with app.app_context():
        # Create a mock class for queries
        class MockQuery:
            @staticmethod
            def all():
                raise Exception("Database error")
        
        # Replace User.query with our mock
        mocker.patch('models.User.query', MockQuery())
        
        result = get_all_users()
        assert result == []