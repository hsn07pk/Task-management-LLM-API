import unittest
from unittest.mock import MagicMock, patch

from flask import Flask

from utils.hypermedia.task_hypermedia import (
    add_task_hypermedia_links,
    generate_tasks_collection_links,
)


class TestTaskHypermedia(unittest.TestCase):

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

    @patch("utils.hypermedia.task_hypermedia.url_for")
    @patch("utils.hypermedia.task_hypermedia.build_standard_links")
    def test_add_task_hypermedia_links_valid_task(self, mock_build_standard_links, mock_url_for):
        # Mock configuration
        mock_build_standard_links.return_value = {"self": {"href": "http://localhost/tasks/123"}}
        mock_url_for.return_value = "http://localhost/tasks/123"

        # Create a valid task dictionary
        task_dict = {
            "id": "123",
            "title": "Test Task",
            "description": "Task for testing hypermedia links",
            "status": "pending",
            "priority": 1,
        }

        # Test adding hypermedia links
        result = add_task_hypermedia_links(task_dict)

        # Verifications
        mock_build_standard_links.assert_called_once_with("task", "123")
        self.assertIn("_links", result)
        self.assertIn("self", result["_links"])
        self.assertIn("update", result["_links"])
        self.assertIn("delete", result["_links"])

    @patch("utils.hypermedia.task_hypermedia.url_for")
    @patch("utils.hypermedia.task_hypermedia.build_standard_links")
    def test_add_task_hypermedia_links_with_project(self, mock_build_standard_links, mock_url_for):
        # Mock configuration
        mock_build_standard_links.return_value = {"self": {"href": "http://localhost/tasks/123"}}

        # Configure url_for behavior based on arguments
        def side_effect(*args, **kwargs):
            if "project_id" in kwargs:
                return f'http://localhost/projects/{kwargs["project_id"]}'
            return "http://localhost/tasks/123"

        mock_url_for.side_effect = side_effect

        # Create a task dictionary with project_id
        task_dict = {
            "id": "123",
            "title": "Test Task",
            "description": "Task for testing hypermedia links",
            "status": "pending",
            "priority": 1,
            "project_id": "456",
        }

        # Test adding hypermedia links
        result = add_task_hypermedia_links(task_dict)

        # Verifications
        self.assertIn("_links", result)
        self.assertIn("project", result["_links"])
        self.assertEqual(result["_links"]["project"]["href"], "http://localhost/projects/456")

    @patch("utils.hypermedia.task_hypermedia.url_for")
    @patch("utils.hypermedia.task_hypermedia.build_standard_links")
    def test_add_task_hypermedia_links_with_assignee(self, mock_build_standard_links, mock_url_for):
        # Mock configuration
        mock_build_standard_links.return_value = {"self": {"href": "http://localhost/tasks/123"}}

        # Configure url_for behavior based on arguments
        def side_effect(*args, **kwargs):
            if "user_id" in kwargs:
                return f'http://localhost/users/{kwargs["user_id"]}'
            return "http://localhost/tasks/123"

        mock_url_for.side_effect = side_effect

        # Create a task dictionary with assignee_id
        task_dict = {
            "id": "123",
            "title": "Test Task",
            "description": "Task for testing hypermedia links",
            "status": "pending",
            "priority": 1,
            "assignee_id": "789",
        }

        # Test adding hypermedia links
        result = add_task_hypermedia_links(task_dict)

        # Verifications
        self.assertIn("_links", result)
        self.assertIn("assignee", result["_links"])
        self.assertEqual(result["_links"]["assignee"]["href"], "http://localhost/users/789")

    @patch("utils.hypermedia.task_hypermedia.url_for")
    @patch("utils.hypermedia.task_hypermedia.build_standard_links")
    def test_add_task_hypermedia_links_with_project_and_assignee(
        self, mock_build_standard_links, mock_url_for
    ):
        # Mock configuration
        mock_build_standard_links.return_value = {"self": {"href": "http://localhost/tasks/123"}}

        # Configure url_for behavior based on arguments
        def side_effect(*args, **kwargs):
            if "project_id" in kwargs:
                return f'http://localhost/projects/{kwargs["project_id"]}'
            elif "user_id" in kwargs:
                return f'http://localhost/users/{kwargs["user_id"]}'
            return "http://localhost/tasks/123"

        mock_url_for.side_effect = side_effect

        # Create a task dictionary with project_id and assignee_id
        task_dict = {
            "id": "123",
            "title": "Test Task",
            "description": "Task for testing hypermedia links",
            "status": "pending",
            "priority": 1,
            "project_id": "456",
            "assignee_id": "789",
        }

        # Test adding hypermedia links
        result = add_task_hypermedia_links(task_dict)

        # Verifications
        self.assertIn("_links", result)
        self.assertIn("project", result["_links"])
        self.assertIn("assignee", result["_links"])
        self.assertEqual(result["_links"]["project"]["href"], "http://localhost/projects/456")
        self.assertEqual(result["_links"]["assignee"]["href"], "http://localhost/users/789")

    def test_add_task_hypermedia_links_invalid_task(self):
        # Test with None
        result = add_task_hypermedia_links(None)
        self.assertEqual(result, None)

        # Test with a non-dictionary
        result = add_task_hypermedia_links("not a dict")
        self.assertEqual(result, "not a dict")

        # Test with a dictionary without id
        result = add_task_hypermedia_links({"title": "No ID Task"})
        self.assertEqual(result, {"title": "No ID Task"})

    @patch("utils.hypermedia.task_hypermedia.url_for")
    @patch("utils.hypermedia.task_hypermedia.build_standard_links")
    def test_generate_tasks_collection_links_no_filters(
        self, mock_build_standard_links, mock_url_for
    ):
        # Mock configuration
        mock_build_standard_links.return_value = {"root": {"href": "http://localhost/"}}
        mock_url_for.return_value = "http://localhost/tasks"

        # Test collection links without filters
        links = generate_tasks_collection_links()

        # Verifications
        mock_build_standard_links.assert_called_once_with("task")
        self.assertIn("create", links)
        self.assertIn("root", links)

    @patch("utils.hypermedia.task_hypermedia.url_for")
    @patch("utils.hypermedia.task_hypermedia.build_standard_links")
    def test_generate_tasks_collection_links_with_filters(
        self, mock_build_standard_links, mock_url_for
    ):
        # Mock configuration
        mock_build_standard_links.return_value = {"root": {"href": "http://localhost/"}}

        # Configure url_for behavior based on arguments
        def side_effect(*args, **kwargs):
            base_url = "http://localhost/tasks"
            query_params = []
            for key, value in kwargs.items():
                if key != "_external":
                    query_params.append(f"{key}={value}")
            if query_params:
                return f"{base_url}?{'&'.join(query_params)}"
            return base_url

        mock_url_for.side_effect = side_effect

        # Test collection links with a filter
        filters = {"status": "in_progress"}
        links = generate_tasks_collection_links(filters)

        # Verifications
        self.assertIn("clear_status_filter", links)
        self.assertEqual(links["clear_status_filter"]["href"], "http://localhost/tasks")

    @patch("utils.hypermedia.task_hypermedia.url_for")
    @patch("utils.hypermedia.task_hypermedia.build_standard_links")
    def test_generate_tasks_collection_links_with_multiple_filters(
        self, mock_build_standard_links, mock_url_for
    ):
        # Mock configuration
        mock_build_standard_links.return_value = {"root": {"href": "http://localhost/"}}

        # Configure url_for behavior based on arguments
        def side_effect(*args, **kwargs):
            base_url = "http://localhost/tasks"
            query_params = []
            for key, value in kwargs.items():
                if key != "_external":
                    query_params.append(f"{key}={value}")
            if query_params:
                return f"{base_url}?{'&'.join(query_params)}"
            return base_url

        mock_url_for.side_effect = side_effect

        # Test collection links with multiple filters
        filters = {
            "status": "in_progress",
            "priority": 1,
            "project_id": "456",
            "assignee_id": "789",
        }
        links = generate_tasks_collection_links(filters)

        # Verifications
        self.assertIn("clear_status_filter", links)
        self.assertIn("clear_priority_filter", links)
        self.assertIn("clear_project_id_filter", links)
        self.assertIn("clear_assignee_id_filter", links)

        # Verify that each filter removal link preserves the other filters
        self.assertIn("priority=1", links["clear_status_filter"]["href"])
        self.assertIn("project_id=456", links["clear_status_filter"]["href"])
        self.assertIn("assignee_id=789", links["clear_status_filter"]["href"])


if __name__ == "__main__":
    unittest.main()
