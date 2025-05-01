from flask import url_for
from utils.hypermedia.link_builder import build_standard_links
from schemas.schemas import TASK_SCHEMA, TASK_UPDATE_SCHEMA

def add_task_hypermedia_links(task_dict):
    """
    Add hypermedia links to a task resource.
    Args:
        task_dict (dict): The task dictionary to add links to
    Returns:
        dict: The task with added _links property
    """
    if not task_dict or not isinstance(task_dict, dict) or "id" not in task_dict:
        return task_dict
    task_with_links = dict(task_dict)
    task_id = str(task_dict["id"])
    links = build_standard_links("task", task_id)
    task_specific = {
        "update": {
            "href": url_for("task_routes.task_operations", task_id=task_id, _external=True),
            "method": "PUT",
            "schema": TASK_UPDATE_SCHEMA
        },
        "delete": {
            "href": url_for("task_routes.task_operations", task_id=task_id, _external=True),
            "method": "DELETE"
        }
    }
    links.update(task_specific)
    if "project_id" in task_dict and task_dict["project_id"]:
        project_id = str(task_dict["project_id"])
        links["project"] = {
            "href": url_for("project_routes.get_project", project_id=project_id, _external=True),
            "method": "GET"
        }
    if "assignee_id" in task_dict and task_dict["assignee_id"]:
        assignee_id = str(task_dict["assignee_id"])
        links["assignee"] = {
            "href": url_for("user_routes.get_user", user_id=assignee_id, _external=True),
            "method": "GET"
        }
    task_with_links["_links"] = links
    return task_with_links

def generate_tasks_collection_links(filters=None):
    """
    Generate links for the tasks collection resource.
    Args:
        filters (dict, optional): Filters applied to the collection
    Returns:
        dict: A dictionary of links for the tasks collection
    """
    links = build_standard_links("task")
    collection_links = {
        "create": {
            "href": url_for("task_routes.create_task", _external=True),
            "method": "POST",
            "schema": TASK_SCHEMA
        }
    }
    links.update(collection_links)
    if filters:
        for key, value in filters.items():
            if value is not None:
                new_filters = {k: v for k, v in filters.items() if k != key and v is not None}
                filter_name = f"clear_{key}_filter"
                if new_filters:
                    links[filter_name] = {
                        "href": url_for("task_routes.get_tasks", **new_filters, _external=True),
                        "method": "GET"
                    }
                else:
                    links[filter_name] = {
                        "href": url_for("task_routes.get_tasks", _external=True),
                        "method": "GET"
                    }
    return links