from flask import url_for

def build_project_links(project):
    """
    Build consistent hypermedia links for a project.
    
    Args:
        project (dict): The project dictionary containing at least project_id
        
    Returns:
        dict: A dictionary of links for the project with appropriate HTTP methods
    """
    project_id = project.get('id') or project.get('project_id')
    if not project_id:
        return {}
    
    # Build comprehensive links for the project
    links = {
        # Self link to get the project
        "self": {
            "href": f"/projects/{project_id}",
            "method": "GET",
            "title": "View this project"
        },
        
        # Update operation
        "update": {
            "href": f"/projects/{project_id}",
            "method": "PUT",
            "title": "Update this project"
        },
        
        # Delete operation
        "delete": {
            "href": f"/projects/{project_id}",
            "method": "DELETE",
            "title": "Delete this project"
        },
        
        # Project tasks
        "tasks": {
            "href": f"/tasks?project_id={project_id}",
            "method": "GET",
            "title": "Tasks in this project"
        },
        
        # Projects collection
        "collection": {
            "href": "/projects",
            "method": "GET",
            "title": "All projects"
        },
        
        # Create new project
        "create": {
            "href": "/projects",
            "method": "POST",
            "title": "Create a new project"
        },
        
        # API root
        "root": {
            "href": "/",
            "method": "GET",
            "title": "API root"
        }
    }
    
    # Add team link if available
    if project.get("team_id"):
        links["team"] = {
            "href": f"/teams/{project['team_id']}",
            "method": "GET",
            "title": "Team assigned to this project"
        }
    
    # Add category link if available
    if project.get("category_id"):
        links["category"] = {
            "href": f"/categories/{project['category_id']}",
            "method": "GET", 
            "title": "Project category"
        }
    
    # Add owner link if available
    if project.get("owner_id"):
        links["owner"] = {
            "href": f"/users/{project['owner_id']}",
            "method": "GET",
            "title": "Project owner"
        }
    
    return links


def build_project_collection_links():
    """
    Build hypermedia links for the projects collection endpoint.
    
    Returns:
        dict: A dictionary of links for the projects collection
    """
    return {
        "self": {
            "href": "/projects",
            "method": "GET",
            "title": "All projects"
        },
        "create": {
            "href": "/projects",
            "method": "POST",
            "title": "Create a new project"
        },
        "root": {
            "href": "/",
            "method": "GET",
            "title": "API root"
        },
        "tasks": {
            "href": "/tasks",
            "method": "GET",
            "title": "All tasks"
        },
        "teams": {
            "href": "/teams",
            "method": "GET",
            "title": "All teams"
        },
        "users": {
            "href": "/users",
            "method": "GET",
            "title": "All users"
        }
    }


def add_project_hypermedia_links(project_dict):
    """
    Add consistent hypermedia links to a project resource.
    
    Args:
        project_dict (dict): The project dictionary to add links to
        
    Returns:
        dict: The project with added _links property
    """
    if not project_dict or not isinstance(project_dict, dict):
        return project_dict
    
    # Create a deep copy of the project to avoid modifying the original
    project_with_links = dict(project_dict)
    
    # Build the links
    links = build_project_links(project_dict)
    
    # Add the links to the project
    project_with_links["_links"] = links
    
    return project_with_links


def generate_projects_collection_links():
    """
    Generate links for the projects collection resource.
    
    Returns:
        dict: A dictionary of links for the projects collection
    """
    return build_project_collection_links()