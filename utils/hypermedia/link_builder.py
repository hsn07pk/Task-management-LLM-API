from flask import url_for

def build_standard_links(entity_type, entity_id=None):
    links = {}

    def safe_url(route_name, **kwargs):
        try:
            return url_for(route_name, _external=True, **kwargs)
        except:
            return None

    # Root link
    root_href = safe_url("entry_point.api_root")
    if root_href:
        links["root"] = {"href": root_href, "method": "GET"}

    # Collection link
    collections = {
        "task": ["task_routes.get_tasks"],
        "project": ["project_routes.get_all_projects"],
        "team": ["team_routes.get_all_teams", "team_routes.get_teams"],
        "user": ["user_routes.fetch_users", "user_routes.get_users"]
    }
    for route in collections.get(entity_type, []):
        href = safe_url(route)
        if href:
            links["collection"] = {"href": href, "method": "GET"}
            break

    # Self link
    if entity_id:
        routes = {
            "task": ["task_routes.task_operations", "task_routes.get_task"],
            "project": ["project_routes.get_project"],
            "team": ["team_routes.get_team"],
            "user": ["user_routes.get_user"]
        }
        for route in routes.get(entity_type, []):
            href = safe_url(route, **{f"{entity_type}_id": entity_id})
            if href:
                links["self"] = {
                    "href": href,
                    "method": "GET",
                    "title": f"View this {entity_type}"
                }
                break

    # Project-specific operations
    if entity_type == "project":
        if entity_id:
            for op, method, title in [("update_project", "PUT", "Update this project"),
                                       ("delete_project", "DELETE", "Delete this project")]:
                href = safe_url(f"project_routes.{op}", project_id=entity_id)
                if href:
                    links[op.split('_')[0]] = {"href": href, "method": method, "title": title}
            task_href = safe_url("task_routes.get_tasks", project_id=entity_id)
            if task_href:
                links["project_tasks"] = {"href": task_href, "method": "GET", "title": "Tasks in this project"}
        else:
            create_href = safe_url("project_routes.create_project")
            if create_href:
                links["create_project"] = {"href": create_href, "method": "POST", "title": "Create a new project"}

    # Related resources
    for label, route_names in {
        "projects": ["project_routes.get_all_projects"],
        "tasks": ["task_routes.get_tasks"],
        "teams": ["team_routes.get_all_teams", "team_routes.get_teams"],
        "users": ["user_routes.fetch_users", "user_routes.get_users"]
    }.items():
        for route in route_names:
            href = safe_url(route)
            if href:
                links[label] = {"href": href, "method": "GET", "title": f"All {label}"}
                break

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
