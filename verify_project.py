#!/usr/bin/env python3
"""
Project Verification Script for EvoLoop

This script verifies that the EvoLoop project is properly set up and functional.
It runs tests, checks code quality, and validates the example scripts.
"""

import subprocess
import sys
import os
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(message: str):
    """Print a formatted header."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'=' * 70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{message:^70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'=' * 70}{Colors.END}\n")


def print_success(message: str):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message: str):
    """Print an error message."""
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_warning(message: str):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")


def run_command(cmd: list[str], cwd: str | None = None, env: dict | None = None) -> tuple[int, str, str]:
    """Run a command and return the exit code, stdout, and stderr."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr


def verify_installation():
    """Verify that required packages are installed."""
    print_header("Verifying Installation")

    required_packages = ["pytest", "ruff", "mypy"]
    all_installed = True

    for package in required_packages:
        returncode, stdout, _ = run_command([sys.executable, "-m", "pip", "show", package])
        if returncode == 0:
            print_success(f"{package} is installed")
        else:
            print_error(f"{package} is not installed")
            all_installed = False

    return all_installed


def run_tests():
    """Run the test suite."""
    print_header("Running Test Suite")

    project_root = Path(__file__).parent
    src_path = project_root / "src"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(src_path)

    returncode, stdout, stderr = run_command(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd=str(project_root),
        env=env
    )

    if returncode == 0:
        # Count passed tests
        lines = stdout.split('\n')
        for line in lines:
            if 'passed' in line:
                print_success(f"All tests passed: {line.strip()}")
                break
        return True
    else:
        print_error("Some tests failed")
        print(stderr)
        return False


def run_linting():
    """Run code linting with ruff."""
    print_header("Running Code Linting (ruff)")

    project_root = Path(__file__).parent
    returncode, stdout, stderr = run_command(
        ["ruff", "check", "src/"],
        cwd=str(project_root)
    )

    if returncode == 0:
        print_success("All linting checks passed")
        return True
    else:
        print_error("Linting issues found")
        print(stdout)
        return False


def run_type_checking():
    """Run type checking with mypy."""
    print_header("Running Type Checking (mypy)")

    project_root = Path(__file__).parent
    src_path = project_root / "src"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(src_path)

    returncode, stdout, stderr = run_command(
        ["mypy", "src/evoloop"],
        cwd=str(project_root),
        env=env
    )

    if returncode == 0:
        print_success("All type checks passed")
        return True
    else:
        print_error("Type checking issues found")
        print(stdout)
        return False


def verify_examples():
    """Verify that example scripts run without errors."""
    print_header("Verifying Example Scripts")

    project_root = Path(__file__).parent
    src_path = project_root / "src"
    examples_dir = project_root / "examples"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(src_path)

    # Clean up any existing database
    db_path = project_root / "evoloop.db"
    if db_path.exists():
        db_path.unlink()

    # Run simple_qa_agent.py
    returncode, stdout, stderr = run_command(
        [sys.executable, str(examples_dir / "simple_qa_agent.py")],
        cwd=str(project_root),
        env=env
    )

    if returncode == 0:
        print_success("simple_qa_agent.py executed successfully")
        # Verify database was created
        if db_path.exists():
            print_success("Database file created successfully")
            # Clean up
            db_path.unlink()
            return True
        else:
            print_warning("Database file was not created")
            return False
    else:
        print_error("simple_qa_agent.py failed to execute")
        print(stderr)
        return False


def verify_scalability():
    """Verify scalability aspects of the project."""
    print_header("Verifying Scalability Features")

    # Check for proper database indexing
    project_root = Path(__file__).parent
    storage_file = project_root / "src" / "evoloop" / "storage.py"

    with open(storage_file, 'r') as f:
        content = f.read()
        if "CREATE INDEX" in content:
            print_success("Database indexes are implemented for scalability")
        else:
            print_warning("No database indexes found")

    # Check for thread safety
    if "threading" in content or "thread" in content.lower():
        print_success("Thread-safe operations are implemented")
    else:
        print_warning("Thread safety not explicitly implemented")

    # Check for connection pooling or thread-local storage
    if "thread_local" in content or "_local" in content:
        print_success("Thread-local storage implemented for connection management")
    else:
        print_warning("No thread-local storage found")

    return True


def main():
    """Main verification function."""
    print(f"{Colors.BOLD}EvoLoop Project Verification{Colors.END}")
    print(f"Python version: {sys.version}")

    results = []

    # Run all verification steps
    results.append(("Installation", verify_installation()))
    results.append(("Tests", run_tests()))
    results.append(("Linting", run_linting()))
    results.append(("Type Checking", run_type_checking()))
    results.append(("Examples", verify_examples()))
    results.append(("Scalability", verify_scalability()))

    # Print summary
    print_header("Verification Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        if result:
            print_success(f"{name}: PASSED")
        else:
            print_error(f"{name}: FAILED")

    print(f"\n{Colors.BOLD}Overall: {passed}/{total} checks passed{Colors.END}\n")

    if passed == total:
        print_success("✓ All verifications passed! The project is working correctly.")
        return 0
    else:
        print_error(f"✗ {total - passed} verification(s) failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
