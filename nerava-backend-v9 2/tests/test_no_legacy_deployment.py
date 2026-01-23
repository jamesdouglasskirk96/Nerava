"""
Test that legacy code (server/src/) is not deployed or imported.

This test verifies:
1. app/main_simple.py does not import server/src
2. Deployment configs (Procfile, Dockerfile) don't reference server/src
3. No imports of server/src exist in app/ directory
"""
import os
import re
import ast
from pathlib import Path


def test_main_simple_does_not_import_server_src():
    """Verify app/main_simple.py does not import server/src"""
    backend_dir = Path(__file__).parent.parent
    main_simple_path = backend_dir / "app" / "main_simple.py"
    
    assert main_simple_path.exists(), "app/main_simple.py should exist"
    
    with open(main_simple_path, "r") as f:
        content = f.read()
    
    # Check for imports of server/src
    dangerous_patterns = [
        "from server",
        "import server",
        "server/src",
        "server.src",
        "server/main_simple",
    ]
    
    for pattern in dangerous_patterns:
        assert pattern not in content, (
            f"app/main_simple.py should not contain '{pattern}'. "
            "Legacy code from server/src/ must not be imported."
        )


def test_procfile_uses_correct_entrypoint():
    """Verify Procfile uses app.main_simple:app, not server/src"""
    backend_dir = Path(__file__).parent.parent
    procfile_path = backend_dir / "Procfile"
    
    if not procfile_path.exists():
        # Procfile might be in repo root
        repo_root = backend_dir.parent
        procfile_path = repo_root / "Procfile"
    
    if procfile_path.exists():
        with open(procfile_path, "r") as f:
            content = f.read()
        
        # Should use app.main_simple:app
        assert "app.main_simple:app" in content or "app/main_simple" in content, (
            "Procfile should use app.main_simple:app as entrypoint"
        )
        
        # Should NOT reference server/src
        dangerous_patterns = [
            "server/src",
            "server.src",
            "server/main_simple",
        ]
        
        for pattern in dangerous_patterns:
            assert pattern not in content, (
                f"Procfile should not reference '{pattern}'. "
                "Legacy code paths must not be deployed."
            )


def test_dockerfile_uses_correct_entrypoint():
    """Verify Dockerfile uses app.main_simple:app, not server/src"""
    backend_dir = Path(__file__).parent.parent
    dockerfile_path = backend_dir / "Dockerfile"
    
    if dockerfile_path.exists():
        with open(dockerfile_path, "r") as f:
            content = f.read()
        
        # Should use app.main_simple:app
        assert "app.main_simple:app" in content or "app/main_simple" in content, (
            "Dockerfile should use app.main_simple:app as entrypoint"
        )
        
        # Should NOT reference server/src
        dangerous_patterns = [
            "server/src",
            "server.src",
            "server/main_simple",
        ]
        
        for pattern in dangerous_patterns:
            assert pattern not in content, (
                f"Dockerfile should not reference '{pattern}'. "
                "Legacy code paths must not be deployed."
            )


def test_app_directory_does_not_import_server_src():
    """Verify no files in app/ directory import server/src"""
    backend_dir = Path(__file__).parent.parent
    app_dir = backend_dir / "app"
    
    if not app_dir.exists():
        pytest.skip("app/ directory not found")
    
    dangerous_patterns = [
        re.compile(r"from\s+server"),
        re.compile(r"import\s+server"),
        re.compile(r"server/src"),
        re.compile(r"server\.src"),
    ]
    
    violations = []
    for py_file in app_dir.rglob("*.py"):
        # Skip __pycache__
        if "__pycache__" in str(py_file):
            continue
        
        try:
            with open(py_file, "r") as f:
                content = f.read()
            
            for pattern in dangerous_patterns:
                if pattern.search(content):
                    violations.append((py_file, pattern.pattern))
        except Exception as e:
            # Skip files that can't be read (permissions, etc.)
            continue
    
    assert len(violations) == 0, (
        f"Found {len(violations)} files in app/ directory importing server/src:\n" +
        "\n".join(f"  - {path}: {pattern}" for path, pattern in violations)
    )


def test_legacy_code_has_deployment_guard():
    """Verify legacy code (server/src/routes_square.py) has deployment guard"""
    backend_dir = Path(__file__).parent.parent
    legacy_file = backend_dir / "server" / "src" / "routes_square.py"
    
    if not legacy_file.exists():
        pytest.skip("Legacy file server/src/routes_square.py not found")
    
    with open(legacy_file, "r") as f:
        content = f.read()
    
    # Should have deployment guard that checks ENV
    assert "CRITICAL SECURITY ERROR" in content or "RuntimeError" in content, (
        "Legacy code should have deployment guard that fails in non-local environments"
    )
    
    assert "ENV" in content, (
        "Deployment guard should check ENV variable (not REGION)"
    )







