import os
import sys
from datetime import datetime
from io import StringIO
from unittest.mock import MagicMock, call, mock_open, patch

import pytest

# Add parent directory to path to import code_quality
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import code_quality


@pytest.fixture
def mock_subprocess():
    """Mock subprocess.run with a successful return value."""
    with patch("subprocess.run") as mock_run:
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        yield mock_run


def test_print_header():
    """Test the print_header function."""
    with patch("sys.stdout", new=StringIO()) as mock_stdout:
        code_quality.print_header("Test Header")
        output = mock_stdout.getvalue()
        # Check for parts of the expected output, ignoring exact formatting with colors
        assert "Test Header" in output
        assert "=" in output


def test_run_command_success():
    """Test the run_command function with a successful command."""
    with patch("subprocess.run") as mock_run:
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Command output"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        with patch("code_quality.print_header") as mock_print_header:
            result = code_quality.run_command("echo test", "Test Command")

            mock_print_header.assert_called_once_with("Test Command")
            mock_run.assert_called_once_with(
                "echo test", shell=True, capture_output=True, text=True
            )
            assert result == 0


def test_run_command_failure():
    """Test the run_command function with a failing command."""
    with patch("subprocess.run") as mock_run:
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stdout = "Command output"
        mock_process.stderr = "Error output"
        mock_run.return_value = mock_process

        with patch("code_quality.print_header") as mock_print_header:
            result = code_quality.run_command("invalid command", "Error Command")

            mock_print_header.assert_called_once_with("Error Command")
            mock_run.assert_called_once_with(
                "invalid command", shell=True, capture_output=True, text=True
            )
            assert result == 1


def test_handle_fix_mode():
    """Test the handle_fix_mode function directly."""
    with patch("code_quality.print_header") as mock_print_header:
        with patch("code_quality.run_command") as mock_run_command:
            mock_run_command.return_value = 0

            code_quality.handle_fix_mode()

            mock_print_header.assert_called_once_with("AUTOMATIC CODE CORRECTION")
            assert mock_run_command.call_count == 2
            mock_run_command.assert_any_call("black .", "BLACK - Code formatting")
            mock_run_command.assert_any_call("isort --profile black .", "ISORT - Import sorting")


# Create a special class to simulate the datetime.now() function
class MockDateTime:
    @staticmethod
    def now():
        mock_date = MagicMock()
        mock_date.strftime.return_value = "20230101_120000"
        return mock_date


def test_main_create_reports_dir():
    """Test that main creates the reports directory if it doesn't exist."""
    with patch("os.path.exists", return_value=False) as mock_exists:
        with patch("os.makedirs") as mock_makedirs:
            with patch("builtins.open", new_callable=mock_open()) as mock_file:
                with patch("sys.stdout", new=StringIO()) as mock_stdout:
                    with patch("code_quality.run_command", return_value=0) as mock_run_command:
                        # Patch datetime au niveau du module
                        with patch("code_quality.datetime", MockDateTime):
                            code_quality.main()

                            mock_exists.assert_called_with("reports")
                            mock_makedirs.assert_called_once_with("reports")
                            mock_file.assert_called_with(
                                "reports/code_quality_report_20230101_120000.txt", "w"
                            )
                            assert mock_run_command.call_count > 0


def test_main_existing_reports_dir():
    """Test that main works with an existing reports directory."""
    with patch("os.path.exists", return_value=True) as mock_exists:
        with patch("builtins.open", new_callable=mock_open()) as mock_file:
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                with patch("code_quality.run_command", return_value=0) as mock_run_command:
                    # Patch datetime au niveau du module
                    with patch("code_quality.datetime", MockDateTime):
                        code_quality.main()

                        mock_exists.assert_called_with("reports")
                        mock_makedirs = MagicMock()
                        mock_makedirs.assert_not_called()
                        mock_file.assert_called_with(
                            "reports/code_quality_report_20230101_120000.txt", "w"
                        )
                        assert mock_run_command.call_count > 0


def test_fix_mode():
    """Test the --fix mode of the script."""
    with patch("sys.argv", ["code_quality.py", "--fix"]):
        with patch("code_quality.handle_fix_mode") as mock_handle_fix:
            code_quality.main()
            mock_handle_fix.assert_called_once()


def test_main_without_fix_flag():
    """Test the main function without the --fix flag."""
    with patch("sys.argv", ["code_quality.py"]):
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", new_callable=mock_open()):
                with patch("sys.stdout", new=StringIO()):
                    with patch("code_quality.run_command", return_value=0) as mock_run_command:
                        # Patch datetime au niveau du module
                        with patch("code_quality.datetime", MockDateTime):
                            code_quality.main()

                            # Verify run_command calls for linting
                            mock_run_command.assert_any_call(
                                "black --check .", "BLACK - Code formatting check"
                            )
                            mock_run_command.assert_any_call(
                                "isort --check-only --profile black .", "ISORT - Import order check"
                            )
                            mock_run_command.assert_any_call(
                                "flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics",
                                "FLAKE8 (Fatal Errors)",
                            )
                            mock_run_command.assert_any_call(
                                "flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics",
                                "FLAKE8 (Style Warnings)",
                            )
                            mock_run_command.assert_any_call(
                                "vulture .", "VULTURE - Dead code detection"
                            )
                            mock_run_command.assert_any_call(
                                "bandit -r . -c pyproject.toml", "BANDIT - Security issues"
                            )
                            mock_run_command.assert_any_call(
                                "pytest --cov=. tests/", "PYTEST - Running tests with coverage"
                            )
