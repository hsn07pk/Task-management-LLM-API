from flask import url_for

def build_standard_links(entity_type, entity_id=None, extra_links=None):
    """
    Build a standardized set of hypermedia links for an entity.
    
    Args:
        entity_type (str): The type of entity (task, project, team, user)
        entity_id (str, optional): The ID of the specific entity
        extra_links (dict, optional): Additional links specific to this entity
        
    Returns:
        dict: A dictionary of links with complete HATEOAS support
    """
    links = {
        "root": {
            "href": url_for("entry_point.api_root", _external=True), 
            "method": "GET",
            "title": "API root"
        },
    }

    # Add collection link with appropriate title
    if entity_type == "task":
        links["collection"] = {
            "href": url_for("task_routes.get_tasks", _external=True),
            "method": "GET",
            "title": "All tasks"
        }
    elif entity_type == "project":
        links["collection"] = {
            "href": url_for("project_routes.get_all_projects", _external=True),
            "method": "GET",
            "title": "All projects"
        }
    elif entity_type == "team":
        links["collection"] = {
            "href": url_for("team_routes.get_all_teams", _external=True),
            "method": "GET",
            "title": "All teams"
        }
    elif entity_type == "user":
        links["collection"] = {
            "href": url_for("user_routes.fetch_users", _external=True),
            "method": "GET",
            "title": "All users"
        }

    # Add self link if entity_id is provided with appropriate title
    if entity_id:
        if entity_type == "task":
            links["self"] = {
                "href": url_for("task_routes.task_operations", task_id=entity_id, _external=True),
                "method": "GET",
                "title": "Current task"
            }
        elif entity_type == "project":
            links["self"] = {
                "href": url_for("project_routes.get_project", project_id=entity_id, _external=True),
                "method": "GET",
                "title": "Current project"
            }
        elif entity_type == "team":
            links["self"] = {
                "href": url_for("team_routes.get_team", team_id=entity_id, _external=True),
                "method": "GET",
                "title": "Current team"
            }
        elif entity_type == "user":
            links["self"] = {
                "href": url_for("user_routes.get_user", user_id=entity_id, _external=True),
                "method": "GET",
                "title": "Current user"
            }

    # Add related resources links with methods and titles
    links["tasks"] = {
        "href": url_for("task_routes.get_tasks", _external=True),
        "method": "GET",
        "title": "Browse all tasks"
    }
    links["projects"] = {
        "href": url_for("project_routes.get_all_projects", _external=True),
        "method": "GET",
        "title": "Browse all projects"
    }
    links["teams"] = {
        "href": url_for("team_routes.get_all_teams", _external=True),
        "method": "GET",
        "title": "Browse all teams"
    }
    links["users"] = {
        "href": url_for("user_routes.fetch_users", _external=True),
        "method": "GET",
        "title": "Browse all users"
    }

    # Add contextual create links based on entity type
    if entity_type == "task" and not entity_id:
        links["create_task"] = {
            "href": url_for("task_routes.create_task", _external=True),
            "method": "POST",
            "title": "Create new task",
            "encoding": "application/json"
        }
    elif entity_type == "project" and not entity_id:
        links["create_project"] = {
            "href": url_for("project_routes.create_project", _external=True),
            "method": "POST",
            "title": "Create new project",
            "encoding": "application/json"
        }
    elif entity_type == "team" and not entity_id:
        links["create_team"] = {
            "href": url_for("team_routes.create_team", _external=True),
            "method": "POST",
            "title": "Create new team",
            "encoding": "application/json"
        }
    elif entity_type == "user" and not entity_id:
        links["create_user"] = {
            "href": url_for("user_routes.create_user", _external=True),
            "method": "POST",
            "title": "Create new user",
            "encoding": "application/json"
        }

    # Add entity-specific operations if ID is provided
    if entity_id:
        if entity_type == "task":
            links["update"] = {
                "href": url_for("task_routes.update_task", task_id=entity_id, _external=True),
                "method": "PUT",
                "title": "Update this task",
                "encoding": "application/json"
            }
            links["delete"] = {
                "href": url_for("task_routes.delete_task", task_id=entity_id, _external=True),
                "method": "DELETE",
                "title": "Delete this task"
            }
            links["comments"] = {
                "href": url_for("task_routes.get_task_comments", task_id=entity_id, _external=True),
                "method": "GET",
                "title": "View task comments"
            }
        elif entity_type == "project":
            links["update"] = {
                "href": url_for("project_routes.update_project", project_id=entity_id, _external=True),
                "method": "PUT",
                "title": "Update this project",
                "encoding": "application/json"
            }
            links["delete"] = {
                "href": url_for("project_routes.delete_project", project_id=entity_id, _external=True),
                "method": "DELETE",
                "title": "Delete this project"
            }
            links["tasks"] = {
                "href": url_for("project_routes.get_project_tasks", project_id=entity_id, _external=True),
                "method": "GET",
                "title": "View project tasks"
            }
        elif entity_type == "user":
            links["update"] = {
                "href": url_for("user_routes.update_user", user_id=entity_id, _external=True),
                "method": "PUT",
                "title": "Update this user",
                "encoding": "application/json"
            }
            links["user_tasks"] = {
                "href": url_for("task_routes.get_user_tasks", user_id=entity_id, _external=True),
                "method": "GET",
                "title": "View user's tasks"
            }
            links["user_teams"] = {
                "href": url_for("user_routes.get_user_teams", user_id=entity_id, _external=True),
                "method": "GET",
                "title": "View user's teams"
            }

    # Add extra links if provided
    if extra_links and isinstance(extra_links, dict):
        links.update(extra_links)

    return links