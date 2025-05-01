from flask import url_for
from utils.hypermedia.link_builder import build_standard_links
from schemas.schemas import PROJECT_SCHEMA, PROJECT_UPDATE_SCHEMA

def add_project_hypermedia_links(project_dict):
    """
    Add hypermedia links to a project resource.
    Args:
        project_dict (dict): The project dictionary to add links to
    Returns:
        dict: The project with added _links property
    """
    if not project_dict or not isinstance(project_dict, dict) or "id" not in project_dict:
        return project_dict
    project_with_links = dict(project_dict)
    project_id = str(project_dict["id"])
    links = build_standard_links("project", project_id)
    project_specific = {
        "update": {
            "href": url_for("project_routes.update_project", project_id=project_id, _external=True),
            "method": "PUT",
            "schema": PROJECT_UPDATE_SCHEMA
        },
        "delete": {
            "href": url_for("project_routes.delete_project", project_id=project_id, _external=True),
            "method": "DELETE"
        },
        "tasks": {
            "href": url_for("task_routes.get_tasks", project_id=project_id, _external=True),
            "method": "GET"
        }
    }
    links.update(project_specific)
    project_with_links["_links"] = links
    return project_with_links

def generate_projects_collection_links(filters=None):
    """
    Generate links for the projects collection resource.
    Args:
        filters (dict, optional): Any filters applied to the collection
    Returns:
        dict: A dictionary of links for the projects collection
    """
    links = build_standard_links("project")
    collection_links = {
        "create": {
            "href": url_for("project_routes.create_project", _external=True),
            "method": "POST",
            "schema": PROJECT_SCHEMA
        }
    }
    links.update(collection_links)
    
    # Add filter links if filters are provided
    if filters:
        for key, value in filters.items():
            if value is not None:
                new_filters = {k: v for k, v in filters.items() if k != key and v is not None}
                filter_name = f"clear_{key}_filter"
                if new_filters:
                    links[filter_name] = {
                        "href": url_for("project_routes.get_all_projects", **new_filters, _external=True),
                        "method": "GET"
                    }
                else:
                    links[filter_name] = {
                        "href": url_for("project_routes.get_all_projects", _external=True),
                        "method": "GET"
                    }
    
    return links