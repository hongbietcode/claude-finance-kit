"""Environment detection utilities (Colab, Jupyter, venv, OS, etc.)."""

import os
import platform
import sys
from pathlib import Path


def get_platform() -> str:
    """Return the name of the running operating system."""
    return platform.system()


def get_hosting_service() -> str:
    """Identify cloud service or development environment currently running."""
    try:
        if "google.colab" in sys.modules:
            return "Google Colab"
        if "CODESPACE_NAME" in os.environ:
            return "Github Codespace"
        if "GITPOD_WORKSPACE_CLUSTER_HOST" in os.environ:
            return "Gitpod"
        if "REPLIT_USER" in os.environ:
            return "Replit"
        if "KAGGLE_CONTAINER_NAME" in os.environ:
            return "Kaggle"
        space_host = os.environ.get("SPACE_HOST", "")
        if ".hf.space" in space_host:
            return "Hugging Face Spaces"
    except Exception:
        pass
    return "Local or Unknown"


def is_colab() -> bool:
    """Return True if running on Google Colab."""
    return get_hosting_service() == "Google Colab"


def is_jupyter() -> bool:
    """Return True if running inside a Jupyter notebook or JupyterLab."""
    try:
        shell = get_ipython().__class__.__name__  # type: ignore[name-defined]
        return shell in ("ZMQInteractiveShell",)
    except NameError:
        return False


def detect_venv() -> dict:
    """
    Detect the current virtual environment.

    Returns a dict with keys:
        path (str | None), is_active (bool), type (str), python_exe (str)
    """
    venv_path = None
    is_active = False
    venv_type = "system"
    python_exe = sys.executable

    if "VIRTUAL_ENV" in os.environ:
        venv_path = os.environ["VIRTUAL_ENV"]
        is_active = True
        venv_type = "conda" if "conda" in venv_path.lower() else "venv"
        if os.name == "nt":
            python_exe = os.path.join(venv_path, "Scripts", "python.exe")
        else:
            python_exe = os.path.join(venv_path, "bin", "python")
    elif hasattr(sys, "base_prefix") and sys.prefix != sys.base_prefix:
        venv_path = sys.prefix
        is_active = True
        venv_type = "venv"
    elif "CONDA_PREFIX" in os.environ:
        venv_path = os.environ["CONDA_PREFIX"]
        is_active = True
        venv_type = "conda"
        if os.name == "nt":
            python_exe = os.path.join(venv_path, "python.exe")
        else:
            python_exe = os.path.join(venv_path, "bin", "python")

    return {
        "path": venv_path,
        "is_active": is_active,
        "type": venv_type,
        "python_exe": python_exe,
    }


def is_venv_active() -> bool:
    """Return True if running inside an active virtual environment."""
    return detect_venv()["is_active"]


def get_venv_type() -> str:
    """Return the type of current virtual environment: 'venv', 'conda', or 'system'."""
    return detect_venv()["type"]


def get_python_executable() -> str:
    """Return the path to the Python executable for the current environment."""
    return detect_venv()["python_exe"]


def get_python_version_string() -> str:
    """Return the Python version string, e.g. '3.11'."""
    return f"{sys.version_info.major}.{sys.version_info.minor}"


def get_data_dir() -> Path:
    """Return the user-level data directory (~/.claude_finance_kit)."""
    return Path.home() / ".claude_finance_kit"


def get_path_delimiter() -> str:
    """Return OS-appropriate path delimiter."""
    return "\\" if os.name == "nt" else "/"
