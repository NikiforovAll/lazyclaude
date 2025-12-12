"""Shared pytest fixtures for LazyClaude tests."""

import os
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

FIXTURES_DIR = Path(__file__).parent / "integration" / "fixtures"
FAKE_HOME = Path("/fake/home")


@pytest.fixture
def fake_home(fs: FakeFilesystem) -> Generator[Path, None, None]:
    """Create a fake home directory and patch Path.home() to return it."""
    fs.create_dir(FAKE_HOME)
    os.environ["HOME"] = str(FAKE_HOME)
    os.environ["USERPROFILE"] = str(FAKE_HOME)

    with patch.object(Path, "home", return_value=FAKE_HOME):
        yield FAKE_HOME


@pytest.fixture
def fake_project_root(fs: FakeFilesystem) -> Path:
    """Create a fake project root directory."""
    project = Path("/fake/project")
    fs.create_dir(project)
    return project


@pytest.fixture
def user_config_path(fake_home: Path, fs: FakeFilesystem) -> Path:
    """Create user config directory (~/.claude) with fixtures."""
    user_claude = fake_home / ".claude"
    fs.create_dir(user_claude)

    fs.add_real_directory(
        FIXTURES_DIR / "commands",
        target_path=user_claude / "commands",
        read_only=False,
    )
    fs.add_real_directory(
        FIXTURES_DIR / "agents",
        target_path=user_claude / "agents",
        read_only=False,
    )
    fs.add_real_directory(
        FIXTURES_DIR / "skills",
        target_path=user_claude / "skills",
        read_only=False,
    )

    user_memory_dir = user_claude
    fs.add_real_file(
        FIXTURES_DIR / "memory" / "CLAUDE.md",
        target_path=user_memory_dir / "CLAUDE.md",
        read_only=False,
    )
    fs.add_real_file(
        FIXTURES_DIR / "memory" / "AGENTS.md",
        target_path=user_memory_dir / "AGENTS.md",
        read_only=False,
    )

    fs.add_real_file(
        FIXTURES_DIR / "settings" / "user-settings.json",
        target_path=user_claude / "settings.json",
        read_only=False,
    )

    return user_claude


@pytest.fixture
def user_mcp_config(fake_home: Path, fs: FakeFilesystem) -> Path:
    """Create user-level MCP config (~/.claude.json)."""
    mcp_path = fake_home / ".claude.json"
    fs.add_real_file(
        FIXTURES_DIR / "mcp" / "user.claude.json",
        target_path=mcp_path,
        read_only=False,
    )
    return mcp_path


@pytest.fixture
def project_mcp_config(fake_project_root: Path, fs: FakeFilesystem) -> Path:
    """Create project-level MCP config (.mcp.json)."""
    mcp_path = fake_project_root / ".mcp.json"
    fs.add_real_file(
        FIXTURES_DIR / "mcp" / "project.mcp.json",
        target_path=mcp_path,
        read_only=False,
    )
    return mcp_path


@pytest.fixture
def project_config_path(fake_project_root: Path, fs: FakeFilesystem) -> Path:
    """Create project config directory (./.claude) with fixtures."""
    project_claude = fake_project_root / ".claude"
    fs.create_dir(project_claude)

    fs.add_real_directory(
        FIXTURES_DIR / "project" / "commands",
        target_path=project_claude / "commands",
        read_only=False,
    )
    fs.add_real_directory(
        FIXTURES_DIR / "project" / "agents",
        target_path=project_claude / "agents",
        read_only=False,
    )
    fs.add_real_directory(
        FIXTURES_DIR / "project" / "skills",
        target_path=project_claude / "skills",
        read_only=False,
    )
    fs.add_real_file(
        FIXTURES_DIR / "project" / "CLAUDE.md",
        target_path=project_claude / "CLAUDE.md",
        read_only=False,
    )
    fs.add_real_file(
        FIXTURES_DIR / "settings" / "project-settings.json",
        target_path=project_claude / "settings.json",
        read_only=False,
    )

    return project_claude


@pytest.fixture
def plugins_config(user_config_path: Path, fs: FakeFilesystem) -> Path:
    """Create plugins configuration with installed_plugins.json and plugin directories."""
    plugins_dir = user_config_path / "plugins"
    fs.create_dir(plugins_dir)

    fs.add_real_file(
        FIXTURES_DIR / "plugins" / "installed_plugins.json",
        target_path=plugins_dir / "installed_plugins.json",
        read_only=False,
    )

    # V2 uses cache directory with versioned paths
    cache_dir = plugins_dir / "cache" / "test"
    fs.create_dir(cache_dir)

    fs.add_real_directory(
        FIXTURES_DIR / "plugins" / "example-plugin",
        target_path=cache_dir / "example-plugin" / "1.0.0",
        read_only=False,
    )

    return plugins_dir


@pytest.fixture
def full_user_config(
    user_config_path: Path,
    user_mcp_config: Path,  # noqa: ARG001
    plugins_config: Path,  # noqa: ARG001
) -> Path:
    """Complete user configuration with all customization types."""
    return user_config_path


@pytest.fixture
def full_project_config(
    project_config_path: Path,
    project_mcp_config: Path,  # noqa: ARG001
) -> Path:
    """Complete project configuration."""
    return project_config_path
