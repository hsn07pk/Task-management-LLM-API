#!/usr/bin/env python3
"""
Script to run code quality analysis tools on the project.
"""
import os
import subprocess
import sys
from datetime import datetime

# Colors for console output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_header(text):
    """Display a formatted header."""
    print(f"\n{BOLD}{YELLOW}{'=' * 80}{RESET}")
    print(f"{BOLD}{YELLOW}= {text}{RESET}")
    print(f"{BOLD}{YELLOW}{'=' * 80}{RESET}\n")


def run_command(command, title):
    """Execute a command and display the result."""
    print_header(title)
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"{RED}{result.stderr}{RESET}")
    return result.returncode


def main():
    """Main function that executes all analysis tools."""
    # Create a directory for reports if it doesn't exist
    reports_dir = "reports"
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"{reports_dir}/code_quality_report_{timestamp}.txt"

    # Redirect output to a file
    original_stdout = sys.stdout
    with open(report_file, "w") as f:
        sys.stdout = f

        print(f"Code Quality Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # Run Black (code formatter)
        run_command("black --check .", "BLACK - Code formatting check")

        # Run isort (import sorter)
        run_command("isort --check-only --profile black .", "ISORT - Import order check")

        # Run Flake8 (linter)
        run_command("flake8 .", "FLAKE8 - Code style check")

        # Run Pylint (static analysis)
        run_command(
            "pylint app.py models.py routes validators schemas", "PYLINT - Static code analysis"
        )

        # Run Bandit (security analysis)
        run_command("bandit -r .", "BANDIT - Code security analysis")

        # Run MyPy (type checking)
        run_command("mypy app.py models.py routes validators schemas", "MYPY - Type checking")

        # Run tests with coverage
        run_command("pytest --cov=. tests/", "PYTEST - Running tests with coverage")

    # Restore standard output
    sys.stdout = original_stdout

    print(f"{GREEN}Code quality analysis report generated: {report_file}{RESET}")
    print(f"{YELLOW}To automatically apply formatting corrections, run:{RESET}")
    print(f"{BOLD}python code_quality.py --fix{RESET}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--fix":
        # Automatic correction mode
        print_header("AUTOMATIC CODE CORRECTION")
        run_command("black .", "BLACK - Code formatting")
        run_command("isort --profile black .", "ISORT - Import sorting")
        print(f"{GREEN}Automatic corrections applied.{RESET}")
    else:
        main()
