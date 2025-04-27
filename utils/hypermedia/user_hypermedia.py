# utils/hypermedia/user_hypermedia.py

from flask import url_for
from utils.hypermedia.link_builder import build_standard_links

def generate_user_links(user_id=None):
    """
    Generate hypermedia links for user resources.
    
    Args:
        user_id (str, optional): The user ID
        
    Returns:
        dict: A dictionary of links for the user resource
    """
    links = build_standard_links("user", user_id)
    
    # Add user-specific links if we have a user_id
    if user_id:
        links.update({
            "update": {
                "href": url_for("user_routes.update_user", user_id=user_id, _external=True),
                "method": "PUT"
            },
            "delete": {
                "href": url_for("user_routes.delete_user", user_id=user_id, _external=True),
                "method": "DELETE"
            },
            # Include links to resources this user can access/own
            "user_tasks": {
                "href": url_for("task_routes.get_tasks", assignee_id=user_id, _external=True),
                "method": "GET"
            }
        })
    
    return links