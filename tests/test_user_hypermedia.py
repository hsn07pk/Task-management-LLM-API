import unittest
from unittest.mock import MagicMock, patch

from flask import Flask, url_for

from schemas.schemas import USER_SCHEMA, USER_UPDATE_SCHEMA
from utils.hypermedia.user_hypermedia import (
    add_user_hypermedia_links,
    generate_user_hypermedia_links,
    generate_users_collection_links,
)


class TestUserHypermedia(unittest.TestCase):

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

    def test_add_user_hypermedia_links_valid_user(self):
        # Test with a valid user dictionary
        user_dict = {"id": "123", "username": "testuser", "email": "test@example.com"}

        with patch(
            "utils.hypermedia.user_hypermedia.generate_user_hypermedia_links"
        ) as mock_generate_links:
            mock_generate_links.return_value = {"self": {"href": "/users/123"}}

            result = add_user_hypermedia_links(user_dict)

            # Verify the function was called with correct parameters
            mock_generate_links.assert_called_once_with("123")

            # Verify the result contains the expected links
            self.assertIn("_links", result)
            self.assertEqual(result["_links"], {"self": {"href": "/users/123"}})

            # Verify the original user data is preserved
            self.assertEqual(result["id"], "123")
            self.assertEqual(result["username"], "testuser")
            self.assertEqual(result["email"], "test@example.com")

    def test_add_user_hypermedia_links_invalid_user(self):
        # Test with invalid user dictionaries
        test_cases = [None, {}, {"name": "test"}, "not a dict"]  # Missing id

        for test_case in test_cases:
            result = add_user_hypermedia_links(test_case)
            # Should return the input unchanged
            self.assertEqual(result, test_case)

    @patch("utils.hypermedia.user_hypermedia.url_for")
    @patch("utils.hypermedia.user_hypermedia.build_standard_links")
    def test_generate_user_hypermedia_links_collection(
        self, mock_build_standard_links, mock_url_for
    ):
        # Configure mocks
        mock_build_standard_links.return_value = {"root": {"href": "http://localhost/"}}
        mock_url_for.return_value = "http://localhost/users"

        # Test for collection links (without user_id)
        links = generate_user_hypermedia_links()

        # Verify
        mock_build_standard_links.assert_called_once_with("user", None)
        self.assertIn("create", links)
        self.assertIn("root", links)

        # Verify the create link has the correct schema
        self.assertEqual(links["create"]["schema"], USER_SCHEMA)

    @patch("utils.hypermedia.user_hypermedia.url_for")
    @patch("utils.hypermedia.user_hypermedia.build_standard_links")
    def test_generate_user_hypermedia_links_specific_user(
        self, mock_build_standard_links, mock_url_for
    ):
        # Configure mocks
        mock_build_standard_links.return_value = {"root": {"href": "http://localhost/"}}
        mock_url_for.side_effect = (
            lambda route, _external=False, **kwargs: f'http://localhost/{route.split(".")[-1]}'
        )

        # Test for specific user links
        user_id = "123"
        links = generate_user_hypermedia_links(user_id)

        # Verify
        mock_build_standard_links.assert_called_once_with("user", user_id)

        # Check all expected links are present
        self.assertIn("update", links)
        self.assertIn("delete", links)
        self.assertIn("user_tasks", links)
        self.assertIn("teams", links)

        # Verify the update link has the correct schema
        self.assertEqual(links["update"]["schema"], USER_UPDATE_SCHEMA)

        # Verify the links have correct methods
        self.assertEqual(links["update"]["method"], "PUT")
        self.assertEqual(links["delete"]["method"], "DELETE")
        self.assertEqual(links["user_tasks"]["method"], "GET")
        self.assertEqual(links["teams"]["method"], "GET")

    @patch("utils.hypermedia.user_hypermedia.url_for")
    @patch("utils.hypermedia.user_hypermedia.build_standard_links")
    def test_generate_users_collection_links(self, mock_build_standard_links, mock_url_for):
        # Configure mocks
        mock_build_standard_links.return_value = {"root": {"href": "http://localhost/"}}
        mock_url_for.return_value = "http://localhost/users"

        # Test for users collection links
        links = generate_users_collection_links()

        # Verify
        mock_build_standard_links.assert_called_once_with("user")

        # Check expected links are present
        self.assertIn("create", links)
        self.assertIn("root", links)

        # Verify the create link has the correct properties
        self.assertEqual(links["create"]["method"], "POST")
        self.assertEqual(links["create"]["schema"], USER_SCHEMA)


if __name__ == "__main__":
    unittest.main()
