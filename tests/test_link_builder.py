import unittest
from unittest.mock import MagicMock, patch

from flask import Flask, url_for

from utils.hypermedia.link_builder import (
    add_project_hypermedia_links,
    build_project_links,
    build_standard_links,
)


class TestLinkBuilder(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["SERVER_NAME"] = "localhost"
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.request_context = self.app.test_request_context()
        self.request_context.push()

    def tearDown(self):
        self.request_context.pop()
        self.app_context.pop()

    @patch("utils.hypermedia.link_builder.url_for")
    def test_build_standard_links_task_no_id(self, mock_url_for):
        # Configure the mock to return predictable URLs
        def side_effect(endpoint, **kwargs):
            return f"http://localhost/{endpoint.replace('.', '/')}" + (
                f"/{kwargs.get('task_id', '')}" if "task_id" in kwargs else ""
            )

        mock_url_for.side_effect = side_effect

        # Call the function with an entity type "task" without ID
        links = build_standard_links("task")

        # Verify that the base links are present
        self.assertIn("root", links)
        self.assertIn("collection", links)
        self.assertIn("tasks", links)
        self.assertIn("projects", links)
        self.assertIn("teams", links)
        self.assertIn("users", links)
        self.assertIn("create_task", links)

        # Verify that the "self" link is not present (no ID)
        self.assertNotIn("self", links)

        # Verify HTTP methods
        self.assertEqual(links["collection"]["method"], "GET")
        self.assertEqual(links["create_task"]["method"], "POST")

    @patch("utils.hypermedia.link_builder.url_for")
    def test_build_standard_links_task_with_id(self, mock_url_for):
        # Configure the mock
        def side_effect(endpoint, **kwargs):
            return f"http://localhost/{endpoint.replace('.', '/')}" + (
                f"/{kwargs.get('task_id', '')}" if "task_id" in kwargs else ""
            )

        mock_url_for.side_effect = side_effect

        task_id = "123"
        links = build_standard_links("task", entity_id=task_id)

        # Verify that the "self" link is present with the ID
        self.assertIn("self", links)
        self.assertIn(task_id, links["self"]["href"])

        # Verify that the links specific to a task with ID are present
        self.assertIn("update", links)
        self.assertIn("delete", links)

    @patch("utils.hypermedia.link_builder.url_for")
    def test_build_standard_links_project(self, mock_url_for):
        # Configure the mock
        def side_effect(endpoint, **kwargs):
            return f"http://localhost/{endpoint.replace('.', '/')}" + (
                f"/{kwargs.get('project_id', '')}" if "project_id" in kwargs else ""
            )

        mock_url_for.side_effect = side_effect

        # Test without ID
        links = build_standard_links("project")
        self.assertIn("create_project", links)

        # Test with ID
        project_id = "456"
        links = build_standard_links("project", entity_id=project_id)
        self.assertIn("self", links)
        self.assertIn(project_id, links["self"]["href"])

    @patch("utils.hypermedia.link_builder.url_for")
    def test_build_standard_links_team(self, mock_url_for):
        # Configure the mock
        def side_effect(endpoint, **kwargs):
            return f"http://localhost/{endpoint.replace('.', '/')}" + (
                f"/{kwargs.get('team_id', '')}" if "team_id" in kwargs else ""
            )

        mock_url_for.side_effect = side_effect

        # Test without ID
        links = build_standard_links("team")
        self.assertIn("create_team", links)

        # Test with ID
        team_id = "789"
        links = build_standard_links("team", entity_id=team_id)
        self.assertIn("self", links)
        self.assertIn(team_id, links["self"]["href"])

    @patch("utils.hypermedia.link_builder.url_for")
    def test_build_standard_links_user(self, mock_url_for):
        # Configure the mock
        def side_effect(endpoint, **kwargs):
            return f"http://localhost/{endpoint.replace('.', '/')}" + (
                f"/{kwargs.get('user_id', '')}" if "user_id" in kwargs else ""
            )

        mock_url_for.side_effect = side_effect

        # Test with ID
        user_id = "101"
        links = build_standard_links("user", entity_id=user_id)
        self.assertIn("self", links)
        self.assertIn("user_tasks", links)
        self.assertIn("user_teams", links)
        self.assertIn(user_id, links["self"]["href"])

    @patch("utils.hypermedia.link_builder.url_for")
    def test_build_standard_links_with_extra_links(self, mock_url_for):
        # Configure the mock
        mock_url_for.return_value = "http://localhost/mock"

        # Add additional links
        extra_links = {
            "custom_link": {
                "href": "http://localhost/custom",
                "method": "GET",
                "title": "Custom Link",
            }
        }

        links = build_standard_links("task", extra_links=extra_links)

        # Verify that the custom link is present
        self.assertIn("custom_link", links)
        self.assertEqual(links["custom_link"]["href"], "http://localhost/custom")

    @patch("utils.hypermedia.link_builder.url_for")
    def test_build_project_links_no_id(self, mock_url_for):
        # Configure the mock to return URLs or None
        def side_effect(endpoint, **kwargs):
            if endpoint == "nonexistent.route":
                return None
            return f"http://localhost/{endpoint.replace('.', '/')}"

        mock_url_for.side_effect = side_effect

        links = build_project_links()

        # Verify the base links
        self.assertIn("collection", links)
        self.assertIn("create", links)
        self.assertIn("root", links)

        # Verify that project-specific links are not present
        self.assertNotIn("get", links)
        self.assertNotIn("update", links)
        self.assertNotIn("delete", links)

    @patch("utils.hypermedia.link_builder.url_for")
    def test_safe_url_exception_handling(self, mock_url_for):
        # Configure the mock to raise an exception
        mock_url_for.side_effect = Exception("Route not found")

        # Call build_project_links which uses safe_url internally
        links = build_project_links()

        # Verify that links are None due to exceptions in safe_url
        self.assertIsNone(links.get("collection", {}).get("href"))
        self.assertIsNone(links.get("create", {}).get("href"))

        # Direct test of safe_url in add_project_hypermedia_links
        project_dict = {"id": "123"}
        with patch(
            "utils.hypermedia.link_builder.url_for", side_effect=Exception("Route not found")
        ):
            result = add_project_hypermedia_links(project_dict)

            # Verify that the result contains the project data
            self.assertEqual(result["id"], project_dict["id"])

            # Verify that _links is empty or all href are None
            if "_links" in result:
                for link in result["_links"].values():
                    self.assertIsNone(link.get("href"))

    @patch("utils.hypermedia.link_builder.url_for")
    def test_build_project_links_with_id(self, mock_url_for):
        # Configure the mock
        def side_effect(endpoint, **kwargs):
            return f"http://localhost/{endpoint.replace('.', '/')}" + (
                f"/{kwargs.get('project_id', '')}" if "project_id" in kwargs else ""
            )

        mock_url_for.side_effect = side_effect

        project_id = "123"
        links = build_project_links(project_id)

        # Verify project-specific links
        self.assertIn("get", links)
        self.assertIn("update", links)
        self.assertIn("delete", links)
        self.assertIn("tasks", links)

        # Verify that URLs contain the project ID
        self.assertIn(project_id, links["get"]["href"])
        self.assertIn(project_id, links["update"]["href"])
        self.assertIn(project_id, links["delete"]["href"])

    @patch("utils.hypermedia.link_builder.url_for")
    def test_add_project_hypermedia_links(self, mock_url_for):
        # Configure the mock
        def side_effect(endpoint, **kwargs):
            if endpoint == "nonexistent.route":
                return None
            base = f"http://localhost/{endpoint.replace('.', '/')}"
            if "project_id" in kwargs:
                return f"{base}/{kwargs['project_id']}"
            if "team_id" in kwargs:
                return f"{base}/{kwargs['team_id']}"
            if "user_id" in kwargs:
                return f"{base}/{kwargs['user_id']}"
            return base

        mock_url_for.side_effect = side_effect

        # Create a project dictionary
        project_dict = {"id": "123", "title": "Test Project", "team_id": "456", "owner_id": "789"}

        result = add_project_hypermedia_links(project_dict)

        # Verify that the result contains the project data
        self.assertEqual(result["id"], project_dict["id"])
        self.assertEqual(result["title"], project_dict["title"])

        # Verify that links are added
        self.assertIn("_links", result)
        links = result["_links"]

        # Verify specific links
        self.assertIn("self", links)
        self.assertIn("collection", links)
        self.assertIn("update", links)
        self.assertIn("delete", links)
        self.assertIn("tasks", links)
        self.assertIn("team", links)
        self.assertIn("owner", links)
        self.assertIn("root", links)
        self.assertIn("create", links)

        # Verify that URLs contain the appropriate IDs
        self.assertIn(project_dict["id"], links["self"]["href"])
        self.assertIn(project_dict["team_id"], links["team"]["href"])
        self.assertIn(project_dict["owner_id"], links["owner"]["href"])

    @patch("utils.hypermedia.link_builder.url_for")
    def test_add_project_hypermedia_links_invalid_input(self, mock_url_for):
        # Test with a dictionary without ID
        project_dict = {"title": "Test Project"}
        result = add_project_hypermedia_links(project_dict)
        self.assertEqual(result, project_dict)

        # Test with None
        result = add_project_hypermedia_links(None)
        self.assertIsNone(result)

        # Test with a non-dictionary
        result = add_project_hypermedia_links("not a dict")
        self.assertEqual(result, "not a dict")


if __name__ == "__main__":
    unittest.main()
