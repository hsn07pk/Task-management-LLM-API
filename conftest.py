import pytest
from app import create_app
from models import db, User, Project, Task, Team, Category, StatusEnum, PriorityEnum
import uuid

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        'TESTING': True,
        'CACHE_TYPE': 'SimpleCache',  # Use a simple in-memory cache
        'CACHE_DEFAULT_TIMEOUT': 0  # Disable caching
    })
    return app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture(autouse=True)
def app_context(app):
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()

@pytest.fixture
def test_team(app, test_user):  # Add test_user as a dependency
    team = Team(
        name='Test Team',
        description='A test team',
        lead_id=test_user.user_id  # Add valid lead_id
    )
    db.session.add(team)
    db.session.commit()
    return team

@pytest.fixture
def test_category(app):
    """Create a test category."""
    category = Category(
        name='Test Category',
        description='A test category'
    )
    db.session.add(category)
    db.session.commit()
    return category

@pytest.fixture
def test_user(app):
    """Create a test user."""
    user = User(
        username='testuser',
        email='test@example.com',
        password_hash='test_hash',
        role='member'
    )
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def test_project(app, test_team, test_category):
    """Create a test project."""
    project = Project(
        title='Test Project',
        description='A test project',
        status='planning',
        team_id=test_team.team_id,
        category_id=test_category.category_id
    )
    db.session.add(project)
    db.session.commit()
    return project

@pytest.fixture
def test_task(app, test_user, test_project):
    """Create a test task."""
    task = Task(
        title='Test Task',
        description='A test task description',
        status=StatusEnum.PENDING.value,
        priority=PriorityEnum.LOW.value,
        project_id=test_project.project_id,
        assignee_id=test_user.user_id
    )
    db.session.add(task)
    db.session.commit()
    return task

@pytest.fixture
def test_admin_user(app):
    user = User(
        username='admin_user',
        email='admin@example.com',
        password_hash='test_hash',
        role='admin'
    )
    db.session.add(user)
    db.session.commit()
    return user
