from flask import url_for
from utils.hypermedia.link_builder import build_standard_links
from schemas.schemas import TEAM_SCHEMA, TEAM_UPDATE_SCHEMA, TEAM_MEMBERSHIP_SCHEMA

def generate_team_hypermedia_links(team_id=None, members=False):
    """
    Generate hypermedia links for team resources.
    
    Args:
        team_id (str, optional): The ID of the specific team
        members (bool): Whether to include links to team member resources
        
    Returns:
        dict: A dictionary of links
    """
    links = build_standard_links("team", team_id)
    if team_id:
        team_specific = {
            "update": {
                "href": url_for("team_routes.update_team", team_id=team_id, _external=True),
                "method": "PUT",
                "schema": TEAM_UPDATE_SCHEMA
            },
            "delete": {
                "href": url_for("team_routes.delete_team", team_id=team_id, _external=True),
                "method": "DELETE"
            },
            "members": {
                "href": url_for("team_routes.get_team_members", team_id=team_id, _external=True),
                "method": "GET"
            }
        }
        links.update(team_specific)
    if members:
        member_links = {
            "add_member": {
                "href": url_for("team_routes.add_team_member", team_id=team_id, _external=True),
                "method": "POST",
                "schema": TEAM_MEMBERSHIP_SCHEMA
            }
        }
        links.update(member_links)
    else:
        collection_links = {
            "create": {
                "href": url_for("team_routes.create_team", _external=True),
                "method": "POST",
                "schema": TEAM_SCHEMA
            }
        }
        links.update(collection_links)
    return links

def generate_team_member_links(team_id, user_id=None):
    """
    Generate hypermedia links for team member resources.
    
    Args:
        team_id (str): The team ID
        user_id (str, optional): The user ID of the team member
        
    Returns:
        dict: A dictionary of links
    """
    links = {
        "team": {
            "href": url_for("team_routes.get_team", team_id=team_id, _external=True),
            "method": "GET"
        },
        "members": {
            "href": url_for("team_routes.get_team_members", team_id=team_id, _external=True),
            "method": "GET"
        },
        "root": {
            "href": url_for("entry_point.api_root", _external=True),
            "method": "GET"
        }
    }
    if user_id:
        member_specific = {
            "update": {
                "href": url_for(
                    "team_routes.update_team_member",
                    team_id=team_id,
                    user_id=user_id,
                    _external=True
                ),
                "method": "PUT",
                "schema": TEAM_MEMBERSHIP_SCHEMA
            },
            "delete": {
                "href": url_for(
                    "team_routes.remove_team_member",
                    team_id=team_id,
                    user_id=user_id,
                    _external=True
                ),
                "method": "DELETE"
            },
            "user": {
                "href": url_for("user_routes.get_user", user_id=user_id, _external=True),
                "method": "GET"
            }
        }
        links.update(member_specific)
    else:
        collection_links = {
            "add_member": {
                "href": url_for("team_routes.add_team_member", team_id=team_id, _external=True),
                "method": "POST",
                "schema": TEAM_MEMBERSHIP_SCHEMA
            }
        }
        links.update(collection_links)
    return links