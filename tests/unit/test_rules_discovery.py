"""Tests for project rules discovery."""

from pathlib import Path

from lazyclaude.models.customization import ConfigLevel, CustomizationType
from lazyclaude.services.discovery import ConfigDiscoveryService


class TestRulesDiscovery:
    """Tests for _discover_rules() method."""

    def test_discover_rules_from_project_rules_dir(
        self, fs, fake_home: Path, fake_project_root: Path
    ) -> None:
        """Rules in .claude/rules/ are discovered as MEMORY_FILE type."""
        project_config = fake_project_root / ".claude"
        fs.create_dir(project_config / "rules")
        fs.create_file(
            project_config / "rules" / "code-style.md",
            contents="# Code Style Rules\n\nUse 2-space indentation.",
        )

        service = ConfigDiscoveryService(
            user_config_path=fake_home / ".claude",
            project_config_path=project_config,
        )
        rules = service._discover_rules()

        assert len(rules) == 1
        assert rules[0].name == "code-style.md"
        assert rules[0].type == CustomizationType.MEMORY_FILE
        assert rules[0].level == ConfigLevel.PROJECT
        assert "Code Style Rules" in rules[0].content

    def test_discover_rules_recursive_subdirectories(
        self, fs, fake_home: Path, fake_project_root: Path
    ) -> None:
        """Rules in nested subdirectories are discovered with relative path names."""
        project_config = fake_project_root / ".claude"
        fs.create_dir(project_config / "rules" / "frontend")
        fs.create_dir(project_config / "rules" / "backend")

        fs.create_file(
            project_config / "rules" / "frontend" / "react.md",
            contents="# React Guidelines",
        )
        fs.create_file(
            project_config / "rules" / "backend" / "api.md",
            contents="# API Guidelines",
        )
        fs.create_file(
            project_config / "rules" / "general.md",
            contents="# General Rules",
        )

        service = ConfigDiscoveryService(
            user_config_path=fake_home / ".claude",
            project_config_path=project_config,
        )
        rules = service._discover_rules()

        names = {r.name for r in rules}
        assert len(rules) == 3
        assert "frontend/react.md" in names or "frontend\\react.md" in names
        assert "backend/api.md" in names or "backend\\api.md" in names
        assert "general.md" in names

    def test_discover_rules_empty_directory(
        self, fs, fake_home: Path, fake_project_root: Path
    ) -> None:
        """Empty rules directory returns no rules."""
        project_config = fake_project_root / ".claude"
        fs.create_dir(project_config / "rules")

        service = ConfigDiscoveryService(
            user_config_path=fake_home / ".claude",
            project_config_path=project_config,
        )
        rules = service._discover_rules()

        assert len(rules) == 0

    def test_discover_rules_missing_directory(
        self, fs, fake_home: Path, fake_project_root: Path
    ) -> None:
        """Missing rules directory returns no rules."""
        project_config = fake_project_root / ".claude"
        fs.create_dir(project_config)

        service = ConfigDiscoveryService(
            user_config_path=fake_home / ".claude",
            project_config_path=project_config,
        )
        rules = service._discover_rules()

        assert len(rules) == 0

    def test_discover_rules_ignores_non_md_files(
        self, fs, fake_home: Path, fake_project_root: Path
    ) -> None:
        """Non-.md files in rules directory are ignored."""
        project_config = fake_project_root / ".claude"
        fs.create_dir(project_config / "rules")
        fs.create_file(
            project_config / "rules" / "valid-rule.md",
            contents="# Valid Rule",
        )
        fs.create_file(
            project_config / "rules" / "config.json",
            contents='{"key": "value"}',
        )
        fs.create_file(
            project_config / "rules" / "notes.txt",
            contents="Some notes",
        )

        service = ConfigDiscoveryService(
            user_config_path=fake_home / ".claude",
            project_config_path=project_config,
        )
        rules = service._discover_rules()

        assert len(rules) == 1
        assert rules[0].name == "valid-rule.md"

    def test_discover_rules_with_frontmatter(
        self, fs, fake_home: Path, fake_project_root: Path
    ) -> None:
        """Rules with YAML frontmatter are parsed correctly."""
        project_config = fake_project_root / ".claude"
        fs.create_dir(project_config / "rules")
        fs.create_file(
            project_config / "rules" / "typescript.md",
            contents="""---
paths: src/**/*.ts
---

# TypeScript Rules

Use strict mode.
""",
        )

        service = ConfigDiscoveryService(
            user_config_path=fake_home / ".claude",
            project_config_path=project_config,
        )
        rules = service._discover_rules()

        assert len(rules) == 1
        assert rules[0].name == "typescript.md"
        assert "TypeScript Rules" in rules[0].content

    def test_discover_all_includes_rules(
        self, fs, fake_home: Path, fake_project_root: Path
    ) -> None:
        """discover_all() includes rules from .claude/rules/."""
        user_config = fake_home / ".claude"
        fs.create_dir(user_config)
        project_config = fake_project_root / ".claude"
        fs.create_dir(project_config / "rules")

        fs.create_file(
            project_config / "rules" / "test-rule.md",
            contents="# Test Rule",
        )

        service = ConfigDiscoveryService(
            user_config_path=user_config,
            project_config_path=project_config,
        )
        all_customizations = service.discover_all()

        rule_names = [
            c.name for c in all_customizations if c.type == CustomizationType.MEMORY_FILE
        ]
        assert "test-rule.md" in rule_names
