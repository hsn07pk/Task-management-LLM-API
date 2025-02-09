from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
import uuid

# Initialize SQLAlchemy
db = SQLAlchemy()

# User Model
class User(db.Model):
    __tablename__ = 'USER'
    user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(50), default='member')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_login = db.Column(db.DateTime)
    
    teams = db.relationship('Team', backref='leader', lazy=True)
    tasks = db.relationship('Task', backref='assignee', lazy=True)
    memberships = db.relationship('TeamMembership', backref='user', lazy=True)

# Team Model
class Team(db.Model):
    __tablename__ = 'TEAM'
    team_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    lead_id = db.Column(UUID(as_uuid=True), db.ForeignKey('USER.user_id'))
    
    projects = db.relationship('Project', backref='team', lazy=True)
    memberships = db.relationship('TeamMembership', backref='team', lazy=True)

# Category Model
class Category(db.Model):
    __tablename__ = 'CATEGORY'
    category_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), unique=True, nullable=False)
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
    team_id = db.Column(UUID(as_uuid=True), db.ForeignKey('TEAM.team_id'))
    category_id = db.Column(UUID(as_uuid=True), db.ForeignKey('CATEGORY.category_id'))
    
    tasks = db.relationship('Task', backref='project', lazy=True)

# Task Model
class Task(db.Model):
    __tablename__ = 'TASK'
    task_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')
    priority = db.Column(db.Integer, default=3)
    deadline = db.Column(db.DateTime)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('PROJECT.project_id'))
    assignee_id = db.Column(UUID(as_uuid=True), db.ForeignKey('USER.user_id'))

# Team Membership Model
class TeamMembership(db.Model):
    __tablename__ = 'TEAM_MEMBERSHIP'
    membership_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('USER.user_id'))
    team_id = db.Column(UUID(as_uuid=True), db.ForeignKey('TEAM.team_id'))
    role = db.Column(db.String(50), default='member')

# Function to initialize the database
def init_db(app):
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
