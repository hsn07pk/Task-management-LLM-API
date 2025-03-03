from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from enum import Enum
from werkzeug.security import generate_password_hash, check_password_hash


# Initialize SQLAlchemy
db = SQLAlchemy()

# User Model
class User(db.Model):
    __tablename__ = 'USER'
    user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(50), default='member')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_login = db.Column(db.DateTime)
    
    teams = db.relationship('Team', backref='leader', lazy=True, cascade='save-update')
    tasks = db.relationship('Task', backref='assignee', lazy=True, cascade='save-update')
    memberships = db.relationship('TeamMembership', backref='user', lazy=True, cascade='all, delete-orphan')

# Team Model
class Team(db.Model):
    __tablename__ = 'TEAM'
    team_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    lead_id = db.Column(UUID(as_uuid=True), db.ForeignKey('USER.user_id', ondelete='SET NULL'))
    
    projects = db.relationship('Project', backref='team', lazy=True, cascade='all, delete-orphan')
    memberships = db.relationship('TeamMembership', backref='team', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Category Model
class Category(db.Model):
    __tablename__ = 'CATEGORY'
    category_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#64748b')
    
    projects = db.relationship('Project', backref='category', lazy=True)

# Project Model
class Project(db.Model):
    __tablename__ = 'PROJECT'
    project_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='planning')
    deadline = db.Column(db.DateTime)
    team_id = db.Column(UUID(as_uuid=True), db.ForeignKey('TEAM.team_id', ondelete='CASCADE'))
    category_id = db.Column(UUID(as_uuid=True), db.ForeignKey('CATEGORY.category_id', ondelete='SET NULL'))
    
    tasks = db.relationship('Task', backref='project', lazy=True, cascade='all, delete-orphan')

# Priority Enum
class PriorityEnum(int, Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3

# Status Enum
class StatusEnum(str, Enum):
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'

# Task Model
class Task(db.Model):
    __tablename__ = 'TASK'
    task_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default=StatusEnum.PENDING.value)
    priority = db.Column(db.Integer, default=PriorityEnum.LOW.value)
    deadline = db.Column(db.DateTime)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('PROJECT.project_id', ondelete='CASCADE'))
    assignee_id = db.Column(UUID(as_uuid=True), db.ForeignKey('USER.user_id', ondelete='SET NULL'))

    def __init__(self, title, description=None, priority=PriorityEnum.LOW.value, deadline=None, status=StatusEnum.PENDING.value, project_id=None, assignee_id=None):
        self.title = title
        self.description = description
        self.priority = priority
        self.deadline = deadline
        self.status = status
        self.project_id = project_id
        self.assignee_id = assignee_id

    def to_dict(self):
        return {
            'task_id': str(self.task_id),
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'status': self.status,
            'project_id': str(self.project_id),
            'assignee_id': str(self.assignee_id)
        }

# Team Membership Model
class TeamMembership(db.Model):
    __tablename__ = 'TEAM_MEMBERSHIP'
    membership_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('USER.user_id', ondelete='CASCADE'))
    team_id = db.Column(UUID(as_uuid=True), db.ForeignKey('TEAM.team_id', ondelete='CASCADE'))
    role = db.Column(db.String(50), default='member')

# Function to initialize the database
def init_db(app):
    if app.config.get('TESTING'):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:helloworld123@localhost:5432/task_management_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()

# CRUD Functions
def create_user(username, email, password_hash, role='member'):
    user = User(username=username, email=email, password_hash=password_hash, role=role)
    db.session.add(user)
    db.session.commit()
    return user

def get_user_by_id(user_id):
    return User.query.get(user_id)

def update_user(user_id, **kwargs):
    user = get_user_by_id(user_id)
    if user:
        for key, value in kwargs.items():
            setattr(user, key, value)
        db.session.commit()
    return user

def delete_user(user_id):
    user = get_user_by_id(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
    return user

def get_all_users():
    return User.query.all()

def create_team(name, description, lead_id):
    team = Team(name=name, description=description, lead_id=lead_id)
    db.session.add(team)
    db.session.commit()
    return team

def assign_task(title, description, priority, project_id, assignee_id):
    task = Task(title=title, description=description, priority=priority, project_id=project_id, assignee_id=assignee_id)
    db.session.add(task)
    db.session.commit()
    return task

def get_project_tasks(project_id):
    return Task.query.filter_by(project_id=project_id).all()

# Task CRUD Functions
def create_task(title, description=None, priority=PriorityEnum.LOW.value, deadline=None, status=StatusEnum.PENDING.value, project_id=None, assignee_id=None):
    task = Task(title=title, description=description, priority=priority, deadline=deadline, status=status, project_id=project_id, assignee_id=assignee_id)
    db.session.add(task)
    db.session.commit()
    return task

def get_task(task_id):
    return Task.query.get(task_id)

def get_all_tasks(project_id=None, assignee_id=None, status=None):
    query = Task.query
    if project_id:
        query = query.filter_by(project_id=project_id)
    if assignee_id:
        query = query.filter_by(assignee_id=assignee_id)
    if status:
        query = query.filter_by(status=status)
    return query.all()

def update_task(task_id, **kwargs):
    task = get_task(task_id)
    if not task:
        return None
        
    for key, value in kwargs.items():
        setattr(task, key, value)
    db.session.commit()
    return task

def delete_task(task_id):
    task = get_task(task_id)
    if task:
        db.session.delete(task)
        db.session.commit()
        return True
    return False
