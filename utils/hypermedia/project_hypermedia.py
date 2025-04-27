# utils/hypermedia/project_hypermedia.py

from flask import url_for
from utils.hypermedia.link_builder import build_standard_links

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
    
    # Create a deep copy of the project to avoid modifying the original
    project_with_links = dict(project_dict)
    project_id = str(project_dict["id"])
    
    # Use our standard link builder and add project-specific links
    links = build_standard_links("project", project_id)
    
    # Add project-specific links
    project_specific = {
        "update": {
            "href": url_for("project_routes.update_project", project_id=project_id, _external=True),
            "method": "PUT"
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

def generate_projects_collection_links():
    """
    Generate links for the projects collection resource.
    
    Returns:
        dict: A dictionary of links for the projects collection
    """
    links = build_standard_links("project")
    
    # Add collection-specific links
    collection_links = {
        "create": {
            "href": url_for("project_routes.create_project", _external=True),
            "method": "POST"
        }
    }
    links.update(collection_links)
    
    return links