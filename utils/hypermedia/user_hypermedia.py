from flask import url_for
from utils.hypermedia.link_builder import build_standard_links
from schemas.schemas import USER_SCHEMA, USER_UPDATE_SCHEMA

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
