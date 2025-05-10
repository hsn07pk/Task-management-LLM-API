from datetime import datetime
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError


def is_valid_uuid(value):
    try:
        UUID(value)
        return True
    except ValueError:
        return False


from models import PriorityEnum, Project, StatusEnum, Task, User, db


class TaskService:
    @staticmethod
    def create_task(data, user_id):
        try:
            created_by = updated_by = UUID(user_id)
            project_id = UUID(data["project_id"])

            project = Project.query.get(project_id)
            if not project:
                raise ValueError("Invalid project_id: Project not found")

            assignee_id = None
            if "assignee_id" in data and data["assignee_id"]:
                assignee_id = UUID(data["assignee_id"])
                assignee = User.query.get(assignee_id)
                if not assignee:
                    raise ValueError("Invalid assignee_id: User not found")

            deadline = None
            if "deadline" in data and data["deadline"]:
                deadline = datetime.fromisoformat(data["deadline"].replace("Z", "+00:00"))

            status = data.get("status", StatusEnum.PENDING.value)
            if status not in [e.value for e in StatusEnum]:
                raise ValueError(
                    f"Invalid status value. Valid values are: {[e.value for e in StatusEnum]}"
                )

            priority_value = data.get("priority", "LOW")
            if isinstance(priority_value, int):
                if priority_value not in [p.value for p in PriorityEnum]:
                    raise ValueError(
                        f"Invalid priority value. Valid values are: "
                        f"{[e.name for e in PriorityEnum]}"
                    )
                priority = priority_value
            else:
                priority_str = str(priority_value).upper()
                priority = PriorityEnum[priority_str].value

            new_task = Task(
                title=data["title"],
                description=data.get("description"),
                priority=priority,
                deadline=deadline,
                status=status,
                project_id=project_id,
                assignee_id=assignee_id,
                created_by=created_by,
                updated_by=updated_by,
            )

            db.session.add(new_task)
            db.session.commit()
            return new_task.to_dict()
        except (ValueError, KeyError) as e:
            raise ValueError(str(e))
        except SQLAlchemyError as e:
            db.session.rollback()
            raise RuntimeError(f"Database error: {str(e)}")

    @staticmethod
    def get_task(task_id):
        task = Task.query.get(task_id)
        if not task:
            raise ValueError("Task not found")
        return task.to_dict()

    @staticmethod
    def update_task(task_id, data, user_id):
        task = Task.query.get(task_id)
        if not task:
            raise ValueError("Task not found")

        if "title" in data:
            task.title = data["title"]
        if "description" in data:
            task.description = data["description"]
        if "priority" in data:
            priority_value = data["priority"]
            if isinstance(priority_value, int):
                if priority_value not in [p.value for p in PriorityEnum]:
                    raise ValueError(
                        f"Invalid priority value. Valid values are: {[e.name for e in PriorityEnum]}"
                    )
                task.priority = priority_value
            else:
                priority_str = str(priority_value).upper()
                task.priority = PriorityEnum[priority_str].value
        if "status" in data:
            if data["status"] not in [e.value for e in StatusEnum]:
                raise ValueError(
                    f"Invalid status value. Valid values are: " f"{[e.value for e in StatusEnum]}"
                )
            task.status = data["status"]
        if "deadline" in data and data["deadline"]:
            task.deadline = datetime.fromisoformat(data["deadline"].replace("Z", "+00:00"))
        if "assignee_id" in data:
            if data["assignee_id"]:
                assignee_id = UUID(data["assignee_id"])
                assignee = User.query.get(assignee_id)
                if not assignee:
                    raise ValueError("Invalid assignee_id: User not found")
                task.assignee_id = assignee_id
            else:
                task.assignee_id = None

        task.updated_by = UUID(user_id)
        db.session.commit()
        return task.to_dict()

    @staticmethod
    def delete_task(task_id):
        task = Task.query.get(task_id)
        if not task:
            raise ValueError("Task not found")
        db.session.delete(task)
        db.session.commit()

    @staticmethod
    def get_tasks(filters):
        """
        Retrieve tasks based on provided filters.

        Args:
            filters (dict): A dictionary of filters to apply when retrieving tasks.

        Returns:
            list: A list of tasks that match the filters.

        Raises:
            ValueError: If any of the filters are invalid.
        """
        if "project_id" in filters:
            if not is_valid_uuid(filters["project_id"]):
                raise ValueError("Invalid project_id")
            project = Project.query.get(filters["project_id"])
            if not project:
                raise ValueError(f"Project with ID {filters['project_id']} not found")

        if "assignee_id" in filters:
            if not is_valid_uuid(filters["assignee_id"]):
                raise ValueError("Invalid assignee_id")
            assignee = User.query.get(filters["assignee_id"])
            if not assignee:
                raise ValueError(f"User with ID {filters['assignee_id']} not found")

        if "status" in filters:
            if filters["status"] not in [e.value for e in StatusEnum]:
                raise ValueError("Invalid status value")

        if "priority" in filters:
            if filters["priority"] not in [e.value for e in PriorityEnum]:
                raise ValueError("Invalid priority value")

        tasks = Task.query.filter_by(**filters).all()
        return [task.to_dict() for task in tasks]
