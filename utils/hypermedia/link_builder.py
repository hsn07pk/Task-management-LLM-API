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

def build_project_links(project_id=None):
    links = {}

    def safe_url(route_name, **kwargs):
        try:
            return url_for(route_name, _external=True, **kwargs)
        except:
            return None

    links["collection"] = {"href": safe_url("project_routes.get_all_projects"), "method": "GET", "title": "All projects"}
    links["create"] = {"href": safe_url("project_routes.create_project"), "method": "POST", "title": "Create new project"}

    if project_id:
        for op, method, title in [("get_project", "GET", "View this project"),
                                  ("update_project", "PUT", "Update this project"),
                                  ("delete_project", "DELETE", "Delete this project")]:
            href = safe_url(f"project_routes.{op}", project_id=project_id)
            if href:
                links[op.split('_')[0]] = {"href": href, "method": method, "title": title}

        task_href = safe_url("task_routes.get_tasks", project_id=project_id)
        if task_href:
            links["tasks"] = {"href": task_href, "method": "GET", "title": "Tasks in this project"}

    for label, route_names in {
        "teams": ["team_routes.get_all_teams", "team_routes.get_teams"],
        "all_tasks": ["task_routes.get_tasks"]
    }.items():
        for route in route_names:
            href = safe_url(route)
            if href:
                links[label] = {"href": href, "method": "GET", "title": f"All {label.replace('_', ' ')}"}
                break

    root_href = safe_url("entry_point.api_root")
    if root_href:
        links["root"] = {"href": root_href, "method": "GET", "title": "API root"}

    return links

def add_project_hypermedia_links(project_dict):
    if not project_dict or not isinstance(project_dict, dict) or "id" not in project_dict:
        return project_dict

    project_with_links = dict(project_dict)
    project_id = str(project_dict["id"])

    def safe_url(route_name, **kwargs):
        try:
            return url_for(route_name, _external=True, **kwargs)
        except:
            return None

    links = {
        "self": {"href": safe_url("project_routes.get_project", project_id=project_id), "method": "GET"},
        "collection": {"href": safe_url("project_routes.get_all_projects"), "method": "GET"},
        "update": {"href": safe_url("project_routes.update_project", project_id=project_id), "method": "PUT"},
        "delete": {"href": safe_url("project_routes.delete_project", project_id=project_id), "method": "DELETE"},
        "tasks": {"href": safe_url("task_routes.get_tasks", project_id=project_id), "method": "GET", "title": "Tasks in this project"},
    }

    team_id = str(project_dict.get("team_id")) if project_dict.get("team_id") else None
    if team_id:
        links["team"] = {"href": safe_url("team_routes.get_team", team_id=team_id), "method": "GET", "title": "Team assigned to this project"}

    owner_id = str(project_dict.get("owner_id")) if project_dict.get("owner_id") else None
    if owner_id:
        href = safe_url("user_routes.get_user", user_id=owner_id) or safe_url("user_routes.fetch_user", user_id=owner_id)
        if href:
            links["owner"] = {"href": href, "method": "GET", "title": "Project owner"}

    root_href = safe_url("entry_point.api_root")
    if root_href:
        links["root"] = {"href": root_href, "method": "GET"}

    create_href = safe_url("project_routes.create_project")
    if create_href:
        links["create"] = {"href": create_href, "method": "POST", "title": "Create a new project"}

    project_with_links["_links"] = {k: v for k, v in links.items() if v["href"]}
    return project_with_links
