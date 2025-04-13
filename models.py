import uuid
from datetime import datetime
from enum import Enum

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

# Initialize SQLAlchemy
db = SQLAlchemy()


# User Model
class User(db.Model):
    """
    User model represents a user in the system. It includes information such as username, email, password,
    role, and timestamps for account creation and last login.
    """

    __tablename__ = "USER"

    user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(50), default="member")
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_login = db.Column(db.DateTime)

    teams = db.relationship("Team", backref="leader", lazy=True, cascade="save-update")
    tasks = db.relationship(
        "Task",
        foreign_keys="Task.assignee_id",
        backref="assignee",
        lazy=True,
        cascade="save-update",
    )
    created_tasks = db.relationship(
        "Task", foreign_keys="Task.created_by", backref="creator", lazy=True
    )
    updated_tasks = db.relationship(
        "Task", foreign_keys="Task.updated_by", backref="updater", lazy=True
    )
    memberships = db.relationship(
        "TeamMembership", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        """
        Convert the User object into a dictionary format suitable for JSON serialization.
        Returns:
            dict: Dictionary containing user information.
        """
        try:
            return {
                "user_id": str(self.user_id),  # Convert UUID to string
                "username": self.username,
                "email": self.email,
                "role": self.role,
                "created_at": (
                    self.created_at.isoformat() if self.created_at else None
                ),  # Format datetime
                "last_login": self.last_login.isoformat() if self.last_login else None,
                "_links": {"self": f"/users/{self.user_id}"},
            }
        except Exception as e:
            return {"error": f"Error serializing user: {str(e)}"}


# Team Model
class Team(db.Model):
    """
    Team model represents a team within the system. It includes information such as team name, description,
    and a reference to the team lead (user).
    """

    __tablename__ = "TEAM"

    team_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    lead_id = db.Column(UUID(as_uuid=True), db.ForeignKey("USER.user_id", ondelete="SET NULL"))

    projects = db.relationship("Project", backref="team", lazy=True, cascade="all, delete-orphan")
    memberships = db.relationship(
        "TeamMembership", backref="team", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        """
        Convert the Team object into a dictionary format suitable for JSON serialization.
        Returns:
            dict: Dictionary containing team information.
        """
        try:
            return {
                "team_id": str(self.team_id),
                "name": self.name,
                "description": self.description,
                "lead_id": str(self.lead_id) if self.lead_id else None,
                "_links": {
                    "self": f"/teams/{self.team_id}",
                    "members": f"/teams/{self.team_id}/members",
                },
            }
        except Exception as e:
            return {"error": f"Error serializing team: {str(e)}"}


# Category Model
class Category(db.Model):
    """
    Category model represents a category for projects. It includes a name, description, and color code for
    visual representation.
    """

    __tablename__ = "CATEGORY"

    category_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default="#64748b")

    # Define a single relationship with back_populates to avoid conflicts
    projects = db.relationship("Project", back_populates="category", lazy=True)


# Project Model
class Project(db.Model):
    """
    Project model represents a project within the system. It includes project title, description, status,
    deadline, and relationships with teams and categories.
    """

    __tablename__: str = "PROJECT"

    project_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default="planning")
    deadline = db.Column(db.DateTime)
    team_id = db.Column(UUID(as_uuid=True), db.ForeignKey("TEAM.team_id", ondelete="CASCADE"))
    category_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("CATEGORY.category_id", ondelete="SET NULL")
    )

    # Use back_populates to properly link with Category.projects
    category = db.relationship("Category", back_populates="projects", lazy=True)
    tasks = db.relationship("Task", backref="project", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        """
        Convert the Project object into a dictionary format suitable for JSON serialization.
        Returns:
            dict: Dictionary containing project information.
        """
        try:
            return {
                "project_id": str(self.project_id),
                "title": self.title,
                "description": self.description,
                "status": self.status,
                "deadline": self.deadline.isoformat() if self.deadline else None,
                "team_id": str(self.team_id) if self.team_id else None,
                "category_id": str(self.category_id) if self.category_id else None,
                "_links": {
                    "self": f"/projects/{self.project_id}",
                    "tasks": f"/tasks?project_id={self.project_id}",
                },
            }
        except Exception as e:
            print(f"Error in to_dict: {str(e)}")
            return {"error": f"Error serializing project: {str(e)}"}


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

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# Task Model
class Task(db.Model):
    """
    Task model represents a task within a project. It includes task title, description, priority, status,
    deadlines, and relationships with users (assignees, creators, and updaters).
    """

    __tablename__ = "TASK"

    task_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default=StatusEnum.PENDING.value)
    priority = db.Column(db.Integer, default=PriorityEnum.LOW.value)
    deadline = db.Column(db.DateTime)
    project_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("PROJECT.project_id", ondelete="CASCADE")
    )
    assignee_id = db.Column(UUID(as_uuid=True), db.ForeignKey("USER.user_id", ondelete="SET NULL"))
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey("USER.user_id", ondelete="SET NULL"))
    updated_by = db.Column(UUID(as_uuid=True), db.ForeignKey("USER.user_id", ondelete="SET NULL"))

    def __init__(
        self,
        title,
        description=None,
        priority=PriorityEnum.LOW.value,
        deadline=None,
        status=StatusEnum.PENDING.value,
        project_id=None,
        assignee_id=None,
        created_by=None,
        updated_by=None,
    ):
        """
        Initialize a new Task instance.

        Args:
            title: Task title
            description: Task description
            priority: Task priority
            deadline: Task deadline
            status: Task status
            project_id: ID of the project this task belongs to
            assignee_id: ID of the user assigned to this task
            created_by: ID of the user who created this task
            updated_by: ID of the user who last updated this task
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
        try:
            return {
                "task_id": str(self.task_id),
                "title": self.title,
                "description": self.description,
                "priority": self.priority,
                "deadline": self.deadline.isoformat() if self.deadline else None,
                "status": self.status,
                "project_id": str(self.project_id) if self.project_id else None,
                "assignee_id": str(self.assignee_id) if self.assignee_id else None,
                "created_by": str(self.created_by) if self.created_by else None,
                "updated_by": str(self.updated_by) if self.updated_by else None,
                "_links": {
                    "self": f"/tasks/{self.task_id}",
                    "project": f"/projects/{self.project_id}" if self.project_id else None,
                },
            }
        except Exception as e:
            return {"error": f"Error serializing task: {str(e)}"}


# Team Membership Model
class TeamMembership(db.Model):
    """
    Team Membership model represents a membership record for a user within a team, including the role of
    the user within the team.
    """

    __tablename__ = "TEAM_MEMBERSHIP"

    membership_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("USER.user_id", ondelete="CASCADE"))
    team_id = db.Column(UUID(as_uuid=True), db.ForeignKey("TEAM.team_id", ondelete="CASCADE"))
    role = db.Column(db.String(50), default="member")


# Function to initialize the database
def init_db(app):
    """
    Initialize the database for the Flask application.
    Args:
        app (Flask): The Flask application instance.
    """
    try:
        if app.config.get("TESTING"):
            app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        else:
            app.config["SQLALCHEMY_DATABASE_URI"] = (
                "postgresql://admin:helloworld123@localhost:5432/task_management_db"
            )

        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(app)

        with app.app_context():
            db.create_all()
        return True
    except Exception as e:
        print(f"Database initialization error: {str(e)}")
        return False


# CRUD Functions
def create_user(username, email, password, role="member"):
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
    try:
        password_hash = generate_password_hash(password)  # Hash the password
        user = User(username=username, email=email, password_hash=password_hash, role=role)
        db.session.add(user)
        db.session.commit()
        return user
    except IntegrityError as exc:
        db.session.rollback()
        raise ValueError("Username or email already exists") from exc
    except Exception as e:
        db.session.rollback()
        raise RuntimeError(f"Error creating user: {str(e)}") from e


def get_user_by_id(user_id):
    """
    Retrieve a user by their ID.
    Args:
        user_id (UUID): The ID of the user to retrieve.
    Returns:
        User: The user object, or None if not found.
    """
    try:
        if not isinstance(user_id, uuid.UUID):
            try:
                user_id = uuid.UUID(str(user_id))
            except (ValueError, TypeError):
                return None
        return User.query.get(user_id)
    except Exception as e:
        print(f"Error retrieving user: {str(e)}")
        return None


def update_user(user_id, **kwargs):
    """
    Update a user's details.
    Args:
        user_id (UUID): The ID of the user to update.
        **kwargs: The fields to update with their new values.
    Returns:
        User: The updated User object.
    """
    try:
        user = get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
            else:
                raise ValueError(f"Invalid attribute: {key}")

        db.session.commit()
        return user
    except IntegrityError as exc:
        db.session.rollback()
        raise ValueError("Update violates unique constraints (username or email)") from exc
    except Exception as e:
        db.session.rollback()
        raise RuntimeError(f"Error updating user: {str(e)}") from e


def delete_user(user_id):
    """
    Delete a user from the system.
    Args:
        user_id (UUID): The ID of the user to delete.
    Returns:
        User | None: The deleted User object if found and deleted, otherwise None.
    """
    try:
        user = get_user_by_id(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            return user
        return None
    except Exception as e:
        db.session.rollback()
        raise RuntimeError(f"Error deleting user: {str(e)}") from e


def get_all_users():
    """
    Retrieve all users from the system.
    Returns:
        list: A list of all User objects.
    """
    try:
        return User.query.all()
    except Exception as e:
        print(f"Error retrieving users: {str(e)}")
        return []


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
    try:
        # Verify lead_id exists if provided
        if lead_id:
            lead = get_user_by_id(lead_id)
            if not lead:
                raise ValueError(f"User with ID {lead_id} not found")

        team = Team(name=name, description=description, lead_id=lead_id)
        db.session.add(team)
        db.session.commit()
        return team
    except Exception as e:
        db.session.rollback()
        raise RuntimeError(f"Error creating team: {str(e)}") from e


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
    try:
        # Validate project_id
        if project_id:
            project = Project.query.get(project_id)
            if not project:
                raise ValueError(f"Project with ID {project_id} not found")

        # Validate assignee_id
        if assignee_id:
            assignee = get_user_by_id(assignee_id)
            if not assignee:
                raise ValueError(f"User with ID {assignee_id} not found")

        # Validate created_by
        if created_by:
            creator = get_user_by_id(created_by)
            if not creator:
                raise ValueError(f"User with ID {created_by} not found")

        # Validate priority
        try:
            priority_value = int(priority)
            if priority_value not in [e.value for e in PriorityEnum]:
                raise ValueError(f"Invalid priority value: {priority}")
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Priority must be a valid integer: {priority}") from exc

        task = Task(
            title=title,
            description=description,
            priority=priority,
            project_id=project_id,
            assignee_id=assignee_id,
            created_by=created_by,
        )
        db.session.add(task)
        db.session.commit()
        return task
    except Exception as e:
        db.session.rollback()
        raise RuntimeError(f"Error assigning task: {str(e)}") from e


def get_project_tasks(project_id):
    """
    Retrieve all tasks associated with a specific project.
    Args:
        project_id (UUID): The ID of the project.
    Returns:
        list: A list of Task objects associated with the project.
    """
    try:
        if not isinstance(project_id, uuid.UUID):
            try:
                project_id = uuid.UUID(str(project_id))
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Invalid project ID format: {project_id}") from exc

        # Verify project exists
        project = Project.query.get(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")

        return Task.query.filter_by(project_id=project_id).all()
    except Exception as e:
        print(f"Error retrieving project tasks: {str(e)}")
        return []


def create_task(
    title,
    description=None,
    priority=PriorityEnum.LOW.value,
    deadline=None,
    status=StatusEnum.PENDING.value,
    project_id=None,
    assignee_id=None,
    created_by=None,
    updated_by=None,
):
    """
    Create a new task.

    Args:
        title: Task title
        description: Task description
        priority: Task priority (integer value from PriorityEnum)
        deadline: Task deadline date (datetime)
        status: Task status (string value from StatusEnum)
        project_id: ID of the project
        assignee_id: ID of the user assigned to this task
        created_by: ID of the user who created this task
        updated_by: ID of the user who last updated this task

    Returns:
        Newly created Task instance

    Raises:
        ValueError: If validation fails
        Exception: If database operation fails
    """
    try:
        # Validate title
        if not title or not isinstance(title, str):
            raise ValueError("Task title is required and must be a string")

        # Validate priority
        try:
            priority_value = int(priority)
            if priority_value not in [e.value for e in PriorityEnum]:
                raise ValueError(f"Invalid priority value: {priority}")
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Priority must be a valid integer: {priority}") from exc

        # Validate status
        if status not in [e.value for e in StatusEnum]:
            raise ValueError(f"Invalid status value: {status}")

        # Validate project_id
        if project_id:
            if not isinstance(project_id, uuid.UUID):
                try:
                    project_id = uuid.UUID(str(project_id))
                except (ValueError, TypeError) as exc:
                    raise ValueError(f"Invalid project ID format: {project_id}") from exc

            project = Project.query.get(project_id)
            if not project:
                raise ValueError(f"Project with ID {project_id} not found")

        # Validate assignee_id
        if assignee_id:
            if not isinstance(assignee_id, uuid.UUID):
                try:
                    assignee_id = uuid.UUID(str(assignee_id))
                except (ValueError, TypeError) as exc:
                    raise ValueError(f"Invalid assignee ID format: {assignee_id}") from exc

            assignee = get_user_by_id(assignee_id)
            if not assignee:
                raise ValueError(f"User with ID {assignee_id} not found")

        # Validate created_by
        if created_by:
            if not isinstance(created_by, uuid.UUID):
                try:
                    created_by = uuid.UUID(str(created_by))
                except (ValueError, TypeError) as exc:
                    raise ValueError(f"Invalid creator ID format: {created_by}") from exc

            creator = get_user_by_id(created_by)
            if not creator:
                raise ValueError(f"User with ID {created_by} not found")

        # Validate updated_by
        if updated_by:
            if not isinstance(updated_by, uuid.UUID):
                try:
                    updated_by = uuid.UUID(str(updated_by))
                except (ValueError, TypeError) as exc:
                    raise ValueError(f"Invalid updater ID format: {updated_by}") from exc

            updater = get_user_by_id(updated_by)
            if not updater:
                raise ValueError(f"User with ID {updated_by} not found")

        task = Task(
            title=title,
            description=description,
            priority=priority,
            deadline=deadline,
            status=status,
            project_id=project_id,
            assignee_id=assignee_id,
            created_by=created_by,
            updated_by=updated_by,
        )
        db.session.add(task)
        db.session.commit()
        return task
    except Exception as e:
        db.session.rollback()
        raise RuntimeError(f"Error creating task: {str(e)}") from e


def get_task(task_id):
    """
    Retrieve a task by its ID.
    Args:
        task_id (UUID): The ID of the task to retrieve.
    Returns:
        Task: The task object, or None if not found.
    """
    try:
        if not isinstance(task_id, uuid.UUID):
            try:
                task_id = uuid.UUID(str(task_id))
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Invalid task ID format: {task_id}") from exc
        return Task.query.get(task_id)
    except Exception as e:
        print(f"Error retrieving task: {str(e)}")
        return None


def delete_task(task_id):
    """
    Delete a task from the system.
    Args:
        task_id (UUID): The ID of the task to delete.
    Returns:
        bool: True if the task was deleted, False otherwise.
    """
    try:
        if not isinstance(task_id, uuid.UUID):
            try:
                task_id = uuid.UUID(str(task_id))
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Invalid task ID format: {task_id}") from exc

        task = get_task(task_id)
        if task:
            db.session.delete(task)
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting task: {str(e)}")
        return False
