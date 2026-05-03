"""Integration test to verify all packages install and work together."""
import subprocess
import sys
import tempfile
import os


def test_monorepo_installation():
    """Verify that all packages can be installed together without version conflicts.
    
    This test ensures that the monorepo packages (mcchallonge, rce2sheet, 
    mcrobotcombatevents) have compatible dependencies and can coexist in 
    the same Python environment.
    """
    # Create a temporary venv
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = os.path.join(tmpdir, "test_venv")
        
        # Create venv
        subprocess.run(
            [sys.executable, "-m", "venv", venv_path],
            check=True,
            capture_output=True,
        )
        
        # Get the python executable in the venv
        if sys.platform == "win32":
            python_exe = os.path.join(venv_path, "Scripts", "python.exe")
        else:
            python_exe = os.path.join(venv_path, "bin", "python")
        
        # Install all packages together with -e flag
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        packages = [
            os.path.join(repo_root, "mcchallonge"),
            os.path.join(repo_root, "rce2sheet"),
            os.path.join(repo_root, "mcrobotcombatevents"),
        ]
        
        install_cmd = [python_exe, "-m", "pip", "install", "-e"] + packages
        result = subprocess.run(install_cmd, capture_output=True, text=True)
        
        # Check for success
        assert result.returncode == 0, (
            f"Monorepo installation failed:\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )
        
        # Verify all packages are importable
        for package_name in ["mcchallonge", "rce2sheet", "mcrobotcombatevents"]:
            check_cmd = [
                python_exe,
                "-c",
                f"import {package_name}; print('{package_name} imported successfully')",
            ]
            result = subprocess.run(check_cmd, capture_output=True, text=True)
            assert (
                result.returncode == 0
            ), f"Failed to import {package_name}: {result.stderr}"
