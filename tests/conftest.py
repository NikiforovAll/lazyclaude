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
def local_mcp_config(fake_home: Path, fs: FakeFilesystem) -> Path:
    """Create local-level MCP config (~/.claude.json with projects section)."""
    mcp_path = fake_home / ".claude.json"
    fs.add_real_file(
        FIXTURES_DIR / "mcp" / "local.claude.json",
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


def _create_benchmark_config(
    fs: FakeFilesystem,
    home: Path,
    project: Path,
    num_commands: int,
    num_agents: int,
    num_skills: int,
    files_per_skill: int,
    num_mcps: int,
    num_hooks: int,
) -> tuple[Path, Path]:
    """Create benchmark configuration with specified counts."""
    import json

    user_claude = home / ".claude"
    fs.create_dir(user_claude / "commands")
    fs.create_dir(user_claude / "agents")
    fs.create_dir(user_claude / "skills")

    project_claude = project / ".claude"
    fs.create_dir(project_claude / "commands")
    fs.create_dir(project_claude / "agents")
    fs.create_dir(project_claude / "skills")

    for i in range(num_commands):
        level = user_claude if i % 2 == 0 else project_claude
        content = f"""---
description: Benchmark command {i}
---
This is benchmark command number {i}.
It has some content to parse.
"""
        fs.create_file(level / "commands" / f"cmd-{i}.md", contents=content)

    for i in range(num_agents):
        level = user_claude if i % 2 == 0 else project_claude
        content = f"""---
description: Benchmark agent {i}
model: sonnet
---
This is benchmark agent number {i}.
"""
        fs.create_file(level / "agents" / f"agent-{i}.md", contents=content)

    for i in range(num_skills):
        level = user_claude if i % 2 == 0 else project_claude
        skill_dir = level / "skills" / f"skill-{i}"
        fs.create_dir(skill_dir)

        skill_content = f"""---
description: Benchmark skill {i}
---
This is benchmark skill number {i}.
"""
        fs.create_file(skill_dir / "SKILL.md", contents=skill_content)

        for j in range(files_per_skill):
            file_content = f"# File {j} for skill {i}\nSome content here.\n" * 10
            fs.create_file(skill_dir / f"file-{j}.py", contents=file_content)

    fs.create_file(user_claude / "CLAUDE.md", contents="# User memory file\n")
    fs.create_file(project_claude / "CLAUDE.md", contents="# Project memory file\n")

    user_mcps: dict[str, dict[str, object]] = {"mcpServers": {}}
    for i in range(num_mcps // 2):
        user_mcps["mcpServers"][f"server-{i}"] = {
            "command": "npx",
            "args": [f"@example/mcp-{i}"],
        }
    fs.create_file(home / ".claude.json", contents=json.dumps(user_mcps))

    project_mcps: dict[str, dict[str, object]] = {"mcpServers": {}}
    for i in range(num_mcps // 2, num_mcps):
        project_mcps["mcpServers"][f"server-{i}"] = {
            "command": "npx",
            "args": [f"@example/mcp-{i}"],
        }
    fs.create_file(project / ".mcp.json", contents=json.dumps(project_mcps))

    user_hooks: dict[str, dict[str, list[dict[str, object]]]] = {"hooks": {}}
    for i in range(num_hooks // 2):
        event_name = f"PreToolUse_{i}"
        user_hooks["hooks"][event_name] = [
            {
                "matcher": f"Tool{i}",
                "hooks": [{"type": "command", "command": f"echo hook-{i}"}],
            }
        ]
    fs.create_file(user_claude / "settings.json", contents=json.dumps(user_hooks))

    project_hooks: dict[str, dict[str, list[dict[str, object]]]] = {"hooks": {}}
    for i in range(num_hooks // 2, num_hooks):
        event_name = f"PostToolUse_{i}"
        project_hooks["hooks"][event_name] = [
            {
                "matcher": f"Tool{i}",
                "hooks": [{"type": "command", "command": f"echo hook-{i}"}],
            }
        ]
    fs.create_file(project_claude / "settings.json", contents=json.dumps(project_hooks))

    return user_claude, project_claude


@pytest.fixture
def benchmark_small_config(
    fake_home: Path, fake_project_root: Path, fs: FakeFilesystem
) -> tuple[Path, Path]:
    """Small benchmark config: ~20 customizations total."""
    return _create_benchmark_config(
        fs=fs,
        home=fake_home,
        project=fake_project_root,
        num_commands=4,
        num_agents=4,
        num_skills=4,
        files_per_skill=2,
        num_mcps=4,
        num_hooks=4,
    )


@pytest.fixture
def benchmark_medium_config(
    fake_home: Path, fake_project_root: Path, fs: FakeFilesystem
) -> tuple[Path, Path]:
    """Medium benchmark config: ~100 customizations total."""
    return _create_benchmark_config(
        fs=fs,
        home=fake_home,
        project=fake_project_root,
        num_commands=20,
        num_agents=20,
        num_skills=20,
        files_per_skill=5,
        num_mcps=20,
        num_hooks=20,
    )


@pytest.fixture
def benchmark_large_config(
    fake_home: Path, fake_project_root: Path, fs: FakeFilesystem
) -> tuple[Path, Path]:
    """Large benchmark config: ~250 customizations total."""
    return _create_benchmark_config(
        fs=fs,
        home=fake_home,
        project=fake_project_root,
        num_commands=50,
        num_agents=50,
        num_skills=50,
        files_per_skill=5,
        num_mcps=50,
        num_hooks=50,
    )
