from flask import url_for
from utils.hypermedia.link_builder import build_standard_links
from schemas.schemas import USER_SCHEMA, USER_UPDATE_SCHEMA

def add_user_hypermedia_links(user_dict):
    """
    Add hypermedia links to a user resource.
    Args:
        user_dict (dict): The user dictionary to add links to
    Returns:
        dict: The user with added _links property
    """
    if not user_dict or not isinstance(user_dict, dict) or "id" not in user_dict:
        return user_dict
    user_with_links = dict(user_dict)
    user_id = str(user_dict["id"])
    user_with_links["_links"] = generate_user_hypermedia_links(user_id)
    return user_with_links

def generate_user_hypermedia_links(user_id=None):
    """
    Generate hypermedia links for user resources.
    Args:
        user_id (str, optional): The user ID
    Returns:
        dict: A dictionary of links for the user resource
    """
    links = build_standard_links("user", user_id)
    if user_id:
        links.update({
            "update": {
                "href": url_for("user_routes.update_user", user_id=user_id, _external=True),
                "method": "PUT",
                "schema": USER_UPDATE_SCHEMA
            },
            "delete": {
                "href": url_for("user_routes.delete_user", user_id=user_id, _external=True),
                "method": "DELETE"
            },
            "user_tasks": {
                "href": url_for("task_routes.get_tasks", assignee_id=user_id, _external=True),
                "method": "GET"
            },
            "teams": {
                "href": url_for("team_routes.get_all_teams", _external=True),
                "method": "GET"
            }
        })
    else:
        links.update({
            "create": {
                "href": url_for("user_routes.create_user", _external=True),
                "method": "POST",
                "schema": USER_SCHEMA
            }
        })
    return links

def generate_users_collection_links():
    """
    Generate links for the users collection resource.
    Returns:
        dict: A dictionary of links for the users collection
    """
    links = build_standard_links("user")
    collection_links = {
        "create": {
            "href": url_for("user_routes.create_user", _external=True),
            "method": "POST",
            "schema": USER_SCHEMA
        }
    }
    links.update(collection_links)
    return links