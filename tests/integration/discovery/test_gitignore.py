"""Integration tests for gitignore support in discovery."""

from pathlib import Path

from lazyclaude.models.customization import CustomizationType
from lazyclaude.services.discovery import ConfigDiscoveryService


def test_claude_md_in_node_modules_is_ignored(tmp_path: Path) -> None:
    """Test that CLAUDE.md files in node_modules are ignored."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    claude_dir = project_root / ".claude"
    claude_dir.mkdir()

    (project_root / "CLAUDE.md").write_text("# Root Memory")

    node_modules = project_root / "node_modules"
    node_modules.mkdir()
    (node_modules / "CLAUDE.md").write_text("# Should be ignored")

    node_lib = node_modules / "some-lib"
    node_lib.mkdir()
    (node_lib / "CLAUDE.md").write_text("# Should also be ignored")

    service = ConfigDiscoveryService(
        user_config_path=tmp_path / ".claude", project_config_path=claude_dir
    )

    memory_files = service.discover_by_type(CustomizationType.MEMORY_FILE)
    claude_mds = [m for m in memory_files if "CLAUDE.md" in m.name]

    assert len(claude_mds) == 1
    assert claude_mds[0].path == project_root / "CLAUDE.md"


def test_custom_gitignore_patterns_are_respected(tmp_path: Path) -> None:
    """Test that custom .gitignore patterns are respected during discovery."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    gitignore = project_root / ".gitignore"
    gitignore.write_text("experiments/\n*.tmp\n")

    claude_dir = project_root / ".claude"
    claude_dir.mkdir()

    (project_root / "CLAUDE.md").write_text("# Root Memory")

    experiments = project_root / "experiments"
    experiments.mkdir()
    (experiments / "CLAUDE.md").write_text("# Experiment - should be ignored")

    (project_root / "test.tmp").write_text("# Temp file")
    (project_root / "CLAUDE.tmp").write_text("# Should be ignored by pattern")

    service = ConfigDiscoveryService(
        user_config_path=tmp_path / ".claude", project_config_path=claude_dir
    )

    memory_files = service.discover_by_type(CustomizationType.MEMORY_FILE)
    file_paths = [str(m.path) for m in memory_files]

    assert str(project_root / "CLAUDE.md") in file_paths
    assert str(experiments / "CLAUDE.md") not in file_paths


def test_commands_in_ignored_directories_are_skipped(tmp_path: Path) -> None:
    """Test that commands in ignored directories are skipped."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    claude_dir = project_root / ".claude"
    claude_dir.mkdir()

    commands_dir = claude_dir / "commands"
    commands_dir.mkdir()
    (commands_dir / "test.md").write_text("---\nname: test\n---\nTest command")

    node_modules = project_root / "node_modules"
    node_modules.mkdir()
    node_claude = node_modules / ".claude"
    node_claude.mkdir()
    node_commands = node_claude / "commands"
    node_commands.mkdir()
    (node_commands / "bad.md").write_text("---\nname: bad\n---\nBad command")

    service = ConfigDiscoveryService(
        user_config_path=tmp_path / ".claude", project_config_path=claude_dir
    )

    commands = service.discover_by_type(CustomizationType.SLASH_COMMAND)
    command_names = [c.name for c in commands]

    assert "test" in command_names
    assert "bad" not in command_names


def test_plugin_preview_respects_plugin_gitignore(tmp_path: Path) -> None:
    """Test that plugin preview respects the plugin's .gitignore."""
    plugin_dir = tmp_path / "test-plugin"
    plugin_dir.mkdir()

    plugin_gitignore = plugin_dir / ".gitignore"
    plugin_gitignore.write_text("drafts/\n")

    commands_dir = plugin_dir / "commands"
    commands_dir.mkdir()
    (commands_dir / "good.md").write_text("---\nname: good\n---\nGood command")

    drafts_dir = plugin_dir / "drafts"
    drafts_dir.mkdir()
    drafts_commands = drafts_dir / "commands"
    drafts_commands.mkdir()
    (drafts_commands / "draft.md").write_text("---\nname: draft\n---\nDraft command")

    service = ConfigDiscoveryService(
        user_config_path=tmp_path / ".claude",
        project_config_path=tmp_path / "project" / ".claude",
    )

    customizations = service.discover_from_directory(plugin_dir)
    command_names = [
        c.name for c in customizations if c.type == CustomizationType.SLASH_COMMAND
    ]

    assert "good" in command_names
    assert "draft" not in command_names


def test_venv_directories_are_ignored(tmp_path: Path) -> None:
    """Test that .venv and venv directories are ignored."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    claude_dir = project_root / ".claude"
    claude_dir.mkdir()

    (project_root / "CLAUDE.md").write_text("# Root Memory")

    for venv_name in [".venv", "venv"]:
        venv_dir = project_root / venv_name
        venv_dir.mkdir()
        (venv_dir / "CLAUDE.md").write_text(f"# {venv_name} - should be ignored")

    service = ConfigDiscoveryService(
        user_config_path=tmp_path / ".claude", project_config_path=claude_dir
    )

    memory_files = service.discover_by_type(CustomizationType.MEMORY_FILE)
    claude_mds = [m for m in memory_files if "CLAUDE.md" in m.name]

    assert len(claude_mds) == 1
    assert claude_mds[0].path == project_root / "CLAUDE.md"


def test_build_artifacts_are_ignored(tmp_path: Path) -> None:
    """Test that build artifacts (build/, dist/) are ignored."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    claude_dir = project_root / ".claude"
    claude_dir.mkdir()

    commands_dir = claude_dir / "commands"
    commands_dir.mkdir()
    (commands_dir / "test.md").write_text("---\nname: test\n---\nTest")

    for build_dir in ["build", "dist", ".eggs"]:
        artifact_dir = project_root / build_dir
        artifact_dir.mkdir()
        artifact_claude = artifact_dir / ".claude"
        artifact_claude.mkdir()
        artifact_commands = artifact_claude / "commands"
        artifact_commands.mkdir()
        (artifact_commands / f"{build_dir}.md").write_text(
            f"---\nname: {build_dir}\n---\nBad"
        )

    service = ConfigDiscoveryService(
        user_config_path=tmp_path / ".claude", project_config_path=claude_dir
    )

    commands = service.discover_by_type(CustomizationType.SLASH_COMMAND)
    command_names = [c.name for c in commands]

    assert "test" in command_names
    assert "build" not in command_names
    assert "dist" not in command_names
    assert ".eggs" not in command_names


def test_ide_directories_are_ignored(tmp_path: Path) -> None:
    """Test that IDE directories (.idea, .vscode, .vs) are ignored."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    claude_dir = project_root / ".claude"
    claude_dir.mkdir()

    (project_root / "CLAUDE.md").write_text("# Root Memory")

    for ide_dir in [".idea", ".vscode", ".vs"]:
        ide_path = project_root / ide_dir
        ide_path.mkdir()
        (ide_path / "CLAUDE.md").write_text(f"# {ide_dir} - should be ignored")

    service = ConfigDiscoveryService(
        user_config_path=tmp_path / ".claude", project_config_path=claude_dir
    )

    memory_files = service.discover_by_type(CustomizationType.MEMORY_FILE)
    claude_mds = [m for m in memory_files if "CLAUDE.md" in m.name]

    assert len(claude_mds) == 1
    assert claude_mds[0].path == project_root / "CLAUDE.md"


def test_rules_in_ignored_directories_are_skipped(tmp_path: Path) -> None:
    """Test that rules in ignored directories are not discovered."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    claude_dir = project_root / ".claude"
    claude_dir.mkdir()

    rules_dir = claude_dir / "rules"
    rules_dir.mkdir()
    (rules_dir / "good-rule.md").write_text("# Good Rule")

    node_modules = project_root / "node_modules"
    node_modules.mkdir()
    node_claude = node_modules / ".claude"
    node_claude.mkdir()
    node_rules = node_claude / "rules"
    node_rules.mkdir()
    (node_rules / "bad-rule.md").write_text("# Bad Rule")

    service = ConfigDiscoveryService(
        user_config_path=tmp_path / ".claude", project_config_path=claude_dir
    )

    all_customizations = service.discover_all()
    rule_names = [
        c.name
        for c in all_customizations
        if c.type == CustomizationType.MEMORY_FILE and "rule" in c.name.lower()
    ]

    assert "good-rule.md" in rule_names
    assert "bad-rule.md" not in rule_names
