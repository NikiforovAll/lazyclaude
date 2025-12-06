"""Entry point for running lazyclaude as a module."""

import argparse
from pathlib import Path

from lazyclaude import __version__
from lazyclaude.app import create_app


def main() -> None:
    """Run the LazyClaude application."""
    parser = argparse.ArgumentParser(
        prog="lazyclaude",
        description="A lazygit-style TUI for visualizing Claude Code customizations",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "-d",
        "--directory",
        type=Path,
        default=None,
        help="Project directory to scan for customizations (default: current directory)",
    )
    parser.add_argument(
        "-u",
        "--user-config",
        type=Path,
        default=None,
        help="Override user config path (default: ~/.claude)",
    )

    args = parser.parse_args()

    project_config_path = None
    if args.directory:
        project_config_path = args.directory / ".claude"

    app = create_app(
        user_config_path=args.user_config,
        project_config_path=project_config_path,
    )
    app.run()


if __name__ == "__main__":
    main()
