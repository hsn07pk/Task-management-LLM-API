import unittest
from unittest.mock import patch

from flask import Flask

from utils.hypermedia.project_hypermedia import (
    add_project_hypermedia_links,
    build_project_collection_links,
    build_project_links,
    generate_projects_collection_links,
)


class TestProjectHypermedia(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["SERVER_NAME"] = "localhost"
        self.ctx = self.app.test_request_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    @patch("utils.hypermedia.project_hypermedia.url_for")
    def test_build_project_links_no_id(self, mock_url_for):
        # When project has no 'id' or 'project_id'
        project = {}
        links = build_project_links(project)
        self.assertEqual(links, {})

    @patch("utils.hypermedia.project_hypermedia.url_for")
    def test_build_project_links_basic(self, mock_url_for):

        project = {"id": "123"}
        links = build_project_links(project)
        self.assertIn("self", links)
        self.assertIn("update", links)
        self.assertIn("delete", links)
        self.assertIn("tasks", links)
        self.assertEqual(links["self"]["href"], "/projects/123")
        self.assertEqual(links["tasks"]["href"], "/tasks?project_id=123")

    @patch("utils.hypermedia.project_hypermedia.url_for")
    def test_build_project_links_with_team_category_owner(self, mock_url_for):
        # side_effect for self, update, delete, tasks
        mock_url_for.side_effect = [
            "/projects/1",
            "/projects/1",
            "/projects/1",
            "/tasks?project_id=1",
        ]
        project = {"id": "1", "team_id": "t1", "category_id": "c1", "owner_id": "o1"}
        links = build_project_links(project)
        # After default keys, check additional keys
        self.assertIn("team", links)
        self.assertIn("category", links)
        self.assertIn("owner", links)
        self.assertEqual(links["team"]["href"], "/teams/t1")
        self.assertEqual(links["category"]["href"], "/categories/c1")
        self.assertEqual(links["owner"]["href"], "/users/o1")

    def test_build_project_collection_links(self):
        links = build_project_collection_links()
        self.assertIn("self", links)
        self.assertIn("create", links)
        self.assertIn("root", links)
        self.assertEqual(links["self"]["href"], "/projects")
        self.assertEqual(links["create"]["method"], "POST")

    def test_add_project_hypermedia_links(self):
        project = {"id": "42", "name": "Test"}
        # monkey-patch build_project_links
        with patch("utils.hypermedia.project_hypermedia.build_project_links") as mock_build:
            mock_build.return_value = {"foo": {"href": "/foo", "method": "GET"}}
            result = add_project_hypermedia_links(project)
        # original data plus _links
        self.assertEqual(result["id"], "42")
        self.assertIn("_links", result)
        self.assertEqual(result["_links"], {"foo": {"href": "/foo", "method": "GET"}})

    def test_generate_projects_collection_links(self):
        links = generate_projects_collection_links()
        # Should return same as build_project_collection_links
        self.assertIn("self", links)
        self.assertIn("create", links)
        self.assertEqual(links["self"]["href"], "/projects")
