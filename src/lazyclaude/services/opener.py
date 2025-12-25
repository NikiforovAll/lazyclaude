"""System opener utilities for files and URLs."""

import platform
import subprocess
import webbrowser
from pathlib import Path


def open_in_file_explorer(path: Path) -> tuple[bool, str | None]:
    """Open a path in the system file explorer.

    Returns:
        Tuple of (success, error_message). If success is True, error_message is None.
    """
    if not path.exists():
        return False, f"Path not found: {path}"

    system = platform.system()
    try:
        if system == "Windows":
            subprocess.run(["explorer", str(path)], check=False)
        elif system == "Darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
        return True, None
    except OSError as e:
        return False, f"Failed to open explorer: {e}"


def open_github_source(repo: str, sub_path: str | None = None) -> None:
    """Open a GitHub repository URL in the default browser.

    Args:
        repo: GitHub repository in "owner/repo" format.
        sub_path: Optional path within the repository to open.
    """
    url = f"https://github.com/{repo}"
    if sub_path:
        url = f"{url}/tree/main/{sub_path}"
    webbrowser.open(url)
