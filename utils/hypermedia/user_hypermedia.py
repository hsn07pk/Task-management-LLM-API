from flask import url_for


def generate_user_links(user_id=None):
    links = {
        "collection": {
            "href": url_for("user_routes.fetch_users", _external=True),
            "rel": "collection",
            "method": "GET",
        },
        "create": {
            "href": url_for("user_routes.create_user", _external=True),
            "rel": "create",
            "method": "POST",
            "schema": "/schemas/user.json",  # You can serve these schemas statically if needed
        },
    }

    if user_id:
        links.update(
            {
                "self": {
                    "href": url_for("user_routes.get_user", user_id=user_id, _external=True),
                    "rel": "self",
                    "method": "GET",
                },
                "update": {
                    "href": url_for("user_routes.update_user", user_id=user_id, _external=True),
                    "rel": "update",
                    "method": "PUT",
                    "schema": "/schemas/user_update.json",
                },
                "delete": {
                    "href": url_for("user_routes.delete_user", user_id=user_id, _external=True),
                    "rel": "delete",
                    "method": "DELETE",
                },
            }
        )
    return links
