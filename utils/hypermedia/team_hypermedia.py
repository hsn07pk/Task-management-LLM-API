from flask import url_for

from schemas.schemas import TEAM_MEMBERSHIP_SCHEMA, TEAM_SCHEMA, TEAM_UPDATE_SCHEMA
from utils.hypermedia.link_builder import build_standard_links


def generate_team_hypermedia_links(team_id=None, members=False):
    """
    Generate hypermedia links for team resources.

    Args:
        team_id (str, optional): The ID of the specific team
        members (bool): Whether to include links to team member resources

    Returns:
        dict: A dictionary of links with HATEOAS compliance
    """
    # Get standard links (root, collection, self, related resources)
    links = build_standard_links("team", team_id)

    # Add collection-level links
    if not team_id:
        collection_links = {
            "create": {
                "href": url_for("team_routes.create_team", _external=True),
                "method": "POST",
                "schema": TEAM_SCHEMA,
                "encoding": "application/json",
                "title": "Create a new team",
            }
        }
        links.update(collection_links)

    # Add resource-level links for a specific team
    if team_id:
        team_specific = {
            "self": {
                "href": url_for("team_routes.get_team", team_id=team_id, _external=True),
                "method": "GET",
                "title": "Get team details",
            },
            "update": {
                "href": url_for("team_routes.update_team", team_id=team_id, _external=True),
                "method": "PUT",
                "schema": TEAM_UPDATE_SCHEMA,
                "encoding": "application/json",
                "title": "Update team details",
            },
            "delete": {
                "href": url_for("team_routes.delete_team", team_id=team_id, _external=True),
                "method": "DELETE",
                "title": "Delete team",
            },
            "members": {
                "href": url_for("team_routes.get_team_members", team_id=team_id, _external=True),
                "method": "GET",
                "title": "List team members",
            },
            "add_member": {
                "href": url_for("team_routes.add_team_member", team_id=team_id, _external=True),
                "method": "POST",
                "schema": TEAM_MEMBERSHIP_SCHEMA,
                "encoding": "application/json",
                "title": "Add a member to team",
            },
        }
        links.update(team_specific)

        # Add project-related links
        links["team_projects"] = {
            "href": url_for("team_routes.get_team_projects", team_id=team_id, _external=True),
            "method": "GET",
            "title": "Get team's projects",
        }

        # Add task-related links
        links["team_tasks"] = {
            "href": url_for("team_routes.get_team_tasks", team_id=team_id, _external=True),
            "method": "GET",
            "title": "Get team's tasks",
        }

    return links


def generate_team_member_links(team_id, user_id=None):
    """
    Generate hypermedia links for team member resources.

    Args:
        team_id (str): The team ID
        user_id (str, optional): The user ID of the team member

    Returns:
        dict: A dictionary of links with HATEOAS compliance
    """
    links = {
        "team": {
            "href": url_for("team_routes.get_team", team_id=team_id, _external=True),
            "method": "GET",
            "title": "Get parent team",
        },
        "members": {
            "href": url_for("team_routes.get_team_members", team_id=team_id, _external=True),
            "method": "GET",
            "title": "List all team members",
        },
        "root": {
            "href": url_for("entry_point.api_root", _external=True),
            "method": "GET",
            "title": "API root",
        },
        "teams": {
            "href": url_for("team_routes.get_all_teams", _external=True),
            "method": "GET",
            "title": "List all teams",
        },
    }

    # Collection-level member links
    if not user_id:
        collection_links = {
            "add_member": {
                "href": url_for("team_routes.add_team_member", team_id=team_id, _external=True),
                "method": "POST",
                "schema": TEAM_MEMBERSHIP_SCHEMA,
                "encoding": "application/json",
                "title": "Add a team member",
            }
        }
        links.update(collection_links)

    # Specific member links
    if user_id:
        member_specific = {
            "self": {
                "href": url_for(
                    "team_routes.get_team_member", team_id=team_id, user_id=user_id, _external=True
                ),
                "method": "GET",
                "title": "Get team member details",
            },
            "update": {
                "href": url_for(
                    "team_routes.update_team_member",
                    team_id=team_id,
                    user_id=user_id,
                    _external=True,
                ),
                "method": "PUT",
                "schema": TEAM_MEMBERSHIP_SCHEMA,
                "encoding": "application/json",
                "title": "Update team member role",
            },
            "delete": {
                "href": url_for(
                    "team_routes.remove_team_member",
                    team_id=team_id,
                    user_id=user_id,
                    _external=True,
                ),
                "method": "DELETE",
                "title": "Remove member from team",
            },
            "user": {
                "href": url_for("user_routes.get_user", user_id=user_id, _external=True),
                "method": "GET",
                "title": "View user profile",
            },
        }
        links.update(member_specific)

    return links


def generate_error_links(context=None):
    """
    Generate contextual error response links.

    Args:
        context (dict, optional): Error context information including entity type and IDs

    Returns:
        dict: A dictionary of appropriate links
    """
    links = {
        "root": {
            "href": url_for("entry_point.api_root", _external=True),
            "method": "GET",
            "title": "API root",
        },
    }

    if context:
        entity_type = context.get("entity_type")
        entity_id = context.get("entity_id")

        if entity_type == "team":
            links.update(generate_team_hypermedia_links(team_id=entity_id))
        elif entity_type == "team_member":
            team_id = context.get("team_id")
            user_id = context.get("user_id")
            links.update(generate_team_member_links(team_id, user_id))

    return links
