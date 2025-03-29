from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from enum import Enum
from werkzeug.security import generate_password_hash

# Initialize SQLAlchemy
db = SQLAlchemy()

# User Model
class User(db.Model):
    """
    User model represents a user in the system. It includes information such as username, email, password,
    role, and timestamps for account creation and last login.
    """
    __tablename__ = 'USER'

    # Unique identifier for the user
    user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # User's unique username
    username = db.Column(db.String(255), unique=True, nullable=False)
    # User's unique email address
    email = db.Column(db.String(255), unique=True, nullable=False)
    # Hashed password for the user
    password_hash = db.Column(db.Text, nullable=False)
    # Role of the user (e.g., member, admin)
    role = db.Column(db.String(50), default='member')
    # Timestamp for when the user account was created
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    # Timestamp for the user's last login
    last_login = db.Column(db.DateTime)

    # Relationships with other models
    teams = db.relationship('Team', backref='leader', lazy=True, cascade='save-update')
    tasks = db.relationship('Task', foreign_keys='Task.assignee_id', backref='assignee', lazy=True, cascade='save-update')
    created_tasks = db.relationship('Task', foreign_keys='Task.created_by', backref='creator', lazy=True)
    updated_tasks = db.relationship('Task', foreign_keys='Task.updated_by', backref='updater', lazy=True)
    memberships = db.relationship('TeamMembership', backref='user', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        """
        Convert the User object into a dictionary format suitable for JSON serialization.

        Returns:
            dict: Dictionary containing user information.
        """
        return {
            'user_id': str(self.user_id),  # Convert UUID to string
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,  # Format datetime
            'last_login': self.last_login.isoformat() if self.last_login else None,
            '_links': {
                'self': f'/users/{self.user_id}'
            }
        }

# Team Model
class Team(db.Model):
    """
    Team model represents a team within the system. It includes information such as team name, description,
    and a reference to the team lead (user).
    """
    __tablename__ = 'TEAM'

    team_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    lead_id = db.Column(UUID(as_uuid=True), db.ForeignKey('USER.user_id', ondelete='SET NULL'))

    # Relationships with other models
    projects = db.relationship('Project', backref='team', lazy=True, cascade='all, delete-orphan')
    memberships = db.relationship('TeamMembership', backref='team', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        """
        Convert the Team object into a dictionary format suitable for JSON serialization.

        Returns:
            dict: Dictionary containing team information.
        """
        return {
            'team_id': str(self.team_id),
            'name': self.name,
            'description': self.description,
            'lead_id': str(self.lead_id) if self.lead_id else None,
            '_links': {
                'self': f'/teams/{self.team_id}',
                'members': f'/teams/{self.team_id}/members'
            }
        }

# Category Model
class Category(db.Model):
    """
    Category model represents a category for projects. It includes a name, description, and color code for 
    visual representation.
    """
    __tablename__ = 'CATEGORY'

    category_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#64748b')

    projects = db.relationship('Project', backref='category_ref', lazy=True)

# Project Model
class Project(db.Model):
    """
    Project model represents a project within the system. It includes project title, description, status, 
    deadline, and relationships with teams and categories.
    """
    __tablename__ = 'PROJECT'

    project_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='planning')
    deadline = db.Column(db.DateTime)
    team_id = db.Column(UUID(as_uuid=True), db.ForeignKey('TEAM.team_id', ondelete='CASCADE'))
    category_id = db.Column(UUID(as_uuid=True), db.ForeignKey('CATEGORY.category_id', ondelete='SET NULL'))
    category = db.relationship('Category', backref='projects_ref', lazy=True)
    tasks = db.relationship('Task', backref='project', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        """
        Convert the Project object into a dictionary format suitable for JSON serialization.

        Returns:
            dict: Dictionary containing project information.
        """
        return {
            'project_id': str(self.project_id),
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'team_id': str(self.team_id) if self.team_id else None,
            'category_id': str(self.category_id) if self.category_id else None,
            '_links': {
                'self': f'/projects/{self.project_id}',
                'tasks': f'/tasks?project_id={self.project_id}'
            }
        }

# Priority Enum
class PriorityEnum(int, Enum):
    """
    Enum for defining task priorities.
    """
    HIGH = 1
    MEDIUM = 2
    LOW = 3

# Status Enum
class StatusEnum(str, Enum):
    """
    Enum for defining task status.
    """
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'

# Task Model
class Task(db.Model):
    """
    Task model represents a task within a project. It includes task title, description, priority, status, 
    deadlines, and relationships with users (assignees, creators, and updaters).
    """
    __tablename__ = 'TASK'

    task_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default=StatusEnum.PENDING.value)
    priority = db.Column(db.Integer, default=PriorityEnum.LOW.value)
    deadline = db.Column(db.DateTime)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('PROJECT.project_id', ondelete='CASCADE'))
    assignee_id = db.Column(UUID(as_uuid=True), db.ForeignKey('USER.user_id', ondelete='SET NULL'))
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('USER.user_id', ondelete='SET NULL'))
    updated_by = db.Column(UUID(as_uuid=True), db.ForeignKey('USER.user_id', ondelete='SET NULL'))

    def __init__(self, title, description=None, priority=PriorityEnum.LOW.value, deadline=None, 
                 status=StatusEnum.PENDING.value, project_id=None, assignee_id=None, 
                 created_by=None, updated_by=None):
        """
        Constructor for creating a new Task.

        Args:
            title (str): The title of the task.
            description (str, optional): The description of the task.
            priority (int, optional): The priority level of the task.
            deadline (datetime, optional): The task's deadline.
            status (str, optional): The current status of the task.
            project_id (UUID, optional): The ID of the related project.
            assignee_id (UUID, optional): The ID of the user assigned to the task.
            created_by (UUID, optional): The ID of the user who created the task.
            updated_by (UUID, optional): The ID of the user who last updated the task.
        """
        self.title = title
        self.description = description
        self.priority = priority
        self.deadline = deadline
        self.status = status
        self.project_id = project_id
        self.assignee_id = assignee_id
        self.created_by = created_by
        self.updated_by = updated_by

    def to_dict(self):
        """
        Convert the Task object into a dictionary format suitable for JSON serialization.

        Returns:
            dict: Dictionary containing task information.
        """
        return {
            'task_id': str(self.task_id),
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'status': self.status,
            'project_id': str(self.project_id) if self.project_id else None,
            'assignee_id': str(self.assignee_id) if self.assignee_id else None,
            'created_by': str(self.created_by) if self.created_by else None,
            'updated_by': str(self.updated_by) if self.updated_by else None,
            '_links': {
                'self': f'/tasks/{self.task_id}',
                'project': f'/projects/{self.project_id}' if self.project_id else None
            }
        }

# Team Membership Model
class TeamMembership(db.Model):
    """
    Team Membership model represents a membership record for a user within a team, including the role of 
    the user within the team.
    """
    __tablename__ = 'TEAM_MEMBERSHIP'

    membership_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('USER.user_id', ondelete='CASCADE'))
    team_id = db.Column(UUID(as_uuid=True), db.ForeignKey('TEAM.team_id', ondelete='CASCADE'))
    role = db.Column(db.String(50), default='member')

# Function to initialize the database
def init_db(app):
    """
    Initialize the database for the Flask application.

    Args:
        app (Flask): The Flask application instance.
    """
    if app.config.get('TESTING'):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # In-memory database for testing
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:helloworld123@localhost:5432/task_management_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()

# CRUD Functions
def create_user(username, email, password, role='member'):
    """
    Create a new user in the system.

    Args:
        username (str): The username of the new user.
        email (str): The email of the new user.
        password (str): The password of the new user.
        role (str, optional): The role of the user (default is 'member').

    Returns:
        User: The created User object.
    """
    password_hash = generate_password_hash(password)  # Hash the password
    user = User(username=username, email=email, password_hash=password_hash, role=role)
    db.session.add(user)
    db.session.commit()
    return user

def get_user_by_id(user_id):
    """
    Retrieve a user by their ID.

    Args:
        user_id (UUID): The ID of the user to retrieve.

    Returns:
        User: The user object, or None if not found.
    """
    return User.query.get(user_id)

def update_user(user_id, **kwargs):
    """
    Update a user's details.

    Args:
        user_id (UUID): The ID of the user to update.
        **kwargs: The fields to update with their new values.

    Returns:
        User: The updated User object.
    """
    user = get_user_by_id(user_id)
    if user:
        for key, value in kwargs.items():
            setattr(user, key, value)
        db.session.commit()
    return user

def delete_user(user_id):
    """
    Delete a user from the system.

    Args:
        user_id (UUID): The ID of the user to delete.

    Returns:
        User: The deleted User object, or None if not found.
    """
    user = get_user_by_id(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
    return user

def get_all_users():
    """
    Retrieve all users from the system.

    Returns:
        list: A list of all User objects.
    """
    return User.query.all()

def create_team(name, description, lead_id):
    """
    Create a new team in the system.

    Args:
        name (str): The name of the team.
        description (str): The description of the team.
        lead_id (UUID): The ID of the user leading the team.

    Returns:
        Team: The created Team object.
    """
    team = Team(name=name, description=description, lead_id=lead_id)
    db.session.add(team)
    db.session.commit()
    return team

def assign_task(title, description, priority, project_id, assignee_id, created_by=None):
    """
    Assign a new task to a user.

    Args:
        title (str): The title of the task.
        description (str): The description of the task.
        priority (int): The priority level of the task.
        project_id (UUID): The ID of the project the task belongs to.
        assignee_id (UUID): The ID of the user assigned to the task.
        created_by (UUID, optional): The ID of the user creating the task.

    Returns:
        Task: The created Task object.
    """
    task = Task(title=title, description=description, priority=priority, project_id=project_id, 
                assignee_id=assignee_id, created_by=created_by)
    db.session.add(task)
    db.session.commit()
    return task

def get_project_tasks(project_id):
    """
    Retrieve all tasks associated with a specific project.

    Args:
        project_id (UUID): The ID of the project.

    Returns:
        list: A list of Task objects associated with the project.
    """
    return Task.query.filter_by(project_id=project_id).all()

# Task CRUD Functions
def create_task(title, description=None, priority=PriorityEnum.LOW.value, deadline=None, 
                status=StatusEnum.PENDING.value, project_id=None, assignee_id=None, 
                created_by=None, updated_by=None):
    """
    Create a new task.

    Args:
        title (str): The title of the task.
        description (str, optional): The description of the task.
        priority (int, optional): The priority level of the task.
        deadline (datetime, optional): The task's deadline.
        status (str, optional): The current status of the task.
        project_id (UUID, optional): The ID of the related project.
        assignee_id (UUID, optional): The ID of the user assigned to the task.
        created_by (UUID, optional): The ID of the user who created the task.
        updated_by (UUID, optional): The ID of the user who last updated the task.

    Returns:
        Task: The created Task object.
    """
    task = Task(title=title, description=description, priority=priority, deadline=deadline, 
                status=status, project_id=project_id, assignee_id=assignee_id, 
                created_by=created_by, updated_by=updated_by)
    db.session.add(task)
    db.session.commit()
    return task

def update_task(task_id, **kwargs):
    """
    Update an existing task.

    Args:
        task_id (UUID): The ID of the task to update.
        **kwargs: The fields to update with their new values.

    Returns:
        Task: The updated Task object.
    """
    task = Task.query.get(task_id)
    if task:
        for key, value in kwargs.items():
            setattr(task, key, value)
        db.session.commit()
    return task

def delete_task(task_id):
    """
    Delete a task from the system.

    Args:
        task_id (UUID): The ID of the task to delete.

    Returns:
        Task: The deleted Task object, or None if not found.
    """
    task = Task.query.get(task_id)
    if task:
        db.session.delete(task)
        db.session.commit()
    return task
