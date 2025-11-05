#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path

def ensure_venv():
    """Ensure we're using the local virtual environment."""
    # Get the directory where this script is located
    BASE_DIR = Path(__file__).resolve().parent
    venv_python = BASE_DIR / 'venv' / 'Scripts' / 'python.exe'
    
    # Check if we're already using the venv Python
    current_python = Path(sys.executable).resolve()
    venv_python_resolved = venv_python.resolve() if venv_python.exists() else None
    
    # If venv Python exists and we're not using it, restart with venv Python
    if venv_python_resolved and current_python != venv_python_resolved:
        import subprocess
        # For Windows, use subprocess to restart with venv Python
        os.chdir(str(BASE_DIR))
        # Build the command: venv_python + manage.py + original args
        cmd = [str(venv_python_resolved), str(BASE_DIR / 'manage.py')] + sys.argv[1:]
        # Use Popen and wait so output displays correctly, don't capture stdout/stderr
        process = subprocess.Popen(cmd, cwd=str(BASE_DIR), stdout=None, stderr=None)
        sys.exit(process.wait())

def main():
    """Run administrative tasks."""
    # Ensure we're using the local venv
    ensure_venv()
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'condorshop_api.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

