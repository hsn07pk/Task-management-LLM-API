from flask import url_for

def build_standard_links(entity_type, entity_id=None, extra_links=None):
    """
    Build a standardized set of hypermedia links for an entity.
    Args:
        entity_type (str): The type of entity (task, project, team, user)
        entity_id (str, optional): The ID of the specific entity
        extra_links (dict, optional): Additional links specific to this entity
    Returns:
        dict: A dictionary of links
    """
    links = {
        "root": {"href": url_for("entry_point.api_root", _external=True)}
    }

    # Add collection link
    if entity_type == "task":
        links["collection"] = {"href": url_for("task_routes.get_tasks", _external=True)}
    elif entity_type == "project":
        links["collection"] = {"href": url_for("project_routes.get_all_projects", _external=True)}
    elif entity_type == "team":
        links["collection"] = {"href": url_for("team_routes.get_all_teams", _external=True)}
    elif entity_type == "user":
        links["collection"] = {"href": url_for("user_routes.fetch_users", _external=True)}

    # Add self link if entity_id is provided
    if entity_id:
        if entity_type == "task":
            links["self"] = {"href": url_for("task_routes.task_operations", task_id=entity_id, _external=True)}
        elif entity_type == "project":
            links["self"] = {"href": url_for("project_routes.get_project", project_id=entity_id, _external=True)}
        elif entity_type == "team":
            links["self"] = {"href": url_for("team_routes.get_team", team_id=entity_id, _external=True)}
        elif entity_type == "user":
            links["self"] = {"href": url_for("user_routes.get_user", user_id=entity_id, _external=True)}

    # Add related resources links
    links["tasks"] = {"href": url_for("task_routes.get_tasks", _external=True)}
    links["projects"] = {"href": url_for("project_routes.get_all_projects", _external=True)}
    links["teams"] = {"href": url_for("team_routes.get_all_teams", _external=True)}
    links["users"] = {"href": url_for("user_routes.fetch_users", _external=True)}

    # Add extra links if provided
    if extra_links and isinstance(extra_links, dict):
        links.update(extra_links)

    return links
