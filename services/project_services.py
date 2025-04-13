from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from models import Project, Team, db


class ProjectService:
    """Service class for project operations."""

    @staticmethod
    def create_project(data):
        """Creates a new project."""
        try:
            # Validate team_id
            team_id = UUID(data["team_id"])
            team = Team.query.get(team_id)
            if not team:
                raise ValueError("Team not found")

            # Handle optional category_id
            category_id = UUID(data["category_id"]) if data.get("category_id") else None

            # Create and save the project
            new_project = Project(
                title=data["title"],
                description=data.get("description"),
                team_id=team_id,
                category_id=category_id,
            )
            db.session.add(new_project)
            db.session.commit()
            return new_project

        except IntegrityError:
            db.session.rollback()
            raise ValueError("Database integrity error")
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error creating project: {str(e)}")

    @staticmethod
    def get_project(project_id):
        """Retrieves a project by its ID."""
        try:
            return Project.query.get(project_id)
        except Exception as e:
            raise Exception(f"Error retrieving project: {str(e)}")

    @staticmethod
    def update_project(project, data):
        """Updates an existing project."""
        try:
            project.title = data.get("title", project.title)
            project.description = data.get("description", project.description)

            if "team_id" in data:
                team_id = UUID(data["team_id"])
                team = Team.query.get(team_id)
                if not team:
                    raise ValueError("Team not found")
                project.team_id = team_id

            project.category_id = UUID(data["category_id"]) if data.get("category_id") else None

            db.session.commit()
            return project

        except IntegrityError:
            db.session.rollback()
            raise ValueError("Database integrity error")
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error updating project: {str(e)}")

    @staticmethod
    def delete_project(project):
        """Deletes an existing project."""
        try:
            db.session.delete(project)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error deleting project: {str(e)}")

    @staticmethod
    def fetch_all_projects():
        """Retrieve all projects from the database."""
        try:
            projects = db.session.query(Project).all()
            if not projects:
                print("No projects found in the database.")  # Debugging log
            return [project.to_dict() for project in projects]
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error retrieving projects: {str(e)}")
