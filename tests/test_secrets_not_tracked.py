"""
Test P0-1: Verify .env files are not tracked in git
"""
import subprocess
import os


def test_env_not_in_git():
    """Test that .env files are not tracked in git"""
    result = subprocess.run(
        ["git", "ls-files", "|", "grep", "-E", "(^|/)\\.env$"],
        shell=True,
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(__file__))
    )
    # Should return empty (no .env files tracked)
    assert result.stdout.strip() == "", "Found .env files tracked in git"


def test_gitignore_has_env_patterns():
    """Test that .gitignore includes .env patterns"""
    gitignore_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".gitignore")
    with open(gitignore_path, "r") as f:
        gitignore_content = f.read()
    
    assert ".env" in gitignore_content
    assert ".env.*" in gitignore_content or "*.env" in gitignore_content


