#!/usr/bin/env python3
"""
Migration runner script for deployment.
Run this separately from the Procfile if migrations are needed.
"""
import subprocess
import sys
import os

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    """Run Alembic migrations to head."""
    try:
        print("Running Alembic migrations...")
        result = subprocess.run(
            ["python", "-m", "alembic", "upgrade", "head"],
            check=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        print("Migrations completed successfully.")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Migration failed with exit code {e.returncode}: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Migration failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

