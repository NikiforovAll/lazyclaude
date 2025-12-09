"""Tests for CustomizationWriter service."""

import sys
from pathlib import Path

import pytest

from lazyclaude.models.customization import (
    ConfigLevel,
    Customization,
    CustomizationType,
)
from lazyclaude.services.writer import CustomizationWriter


class TestCustomizationWriter:
    """Tests for CustomizationWriter."""

    def test_write_slash_command_to_user_level(
        self, fs, fake_home: Path, fake_project_root: Path
    ) -> None:
        user_config = fake_home / ".claude"
        fs.create_dir(user_config)

        test_file = fake_project_root / "test.md"
        fs.create_file(test_file, contents="# Test Command\nTest content")

        customization = Customization(
            name="test",
            type=CustomizationType.SLASH_COMMAND,
            level=ConfigLevel.PROJECT,
            path=test_file,
            content="# Test Command\nTest content",
        )

        writer = CustomizationWriter()
        success, msg = writer.write_customization(
            customization,
            ConfigLevel.USER,
            user_config,
            fake_project_root / ".claude",
        )

        assert success is True
        assert "Copied 'test' to User level" in msg
        target_path = user_config / "commands" / "test.md"
        assert target_path.exists()
        assert target_path.read_text() == "# Test Command\nTest content"

    def test_write_slash_command_preserves_nested_path(
        self, fs, fake_home: Path, fake_project_root: Path
    ) -> None:
        user_config = fake_home / ".claude"
        fs.create_dir(user_config)

        test_file = fake_project_root / "nested" / "deep.md"
        fs.create_file(test_file, contents="# Nested Command")

        customization = Customization(
            name="nested:deep",
            type=CustomizationType.SLASH_COMMAND,
            level=ConfigLevel.PROJECT,
            path=test_file,
            content="# Nested Command",
        )

        writer = CustomizationWriter()
        success, msg = writer.write_customization(
            customization,
            ConfigLevel.USER,
            user_config,
            fake_project_root / ".claude",
        )

        assert success is True
        target_path = user_config / "commands" / "nested" / "deep.md"
        assert target_path.exists()
        assert target_path.read_text() == "# Nested Command"

    def test_write_subagent_to_project_level(
        self, fs, fake_home: Path, fake_project_root: Path
    ) -> None:
        project_config = fake_project_root / ".claude"
        fs.create_dir(project_config)

        test_file = fake_home / ".claude" / "agents" / "test-agent.md"
        fs.create_file(test_file, contents="# Test Agent\nAgent content")

        customization = Customization(
            name="test-agent",
            type=CustomizationType.SUBAGENT,
            level=ConfigLevel.USER,
            path=test_file,
            content="# Test Agent\nAgent content",
        )

        writer = CustomizationWriter()
        success, msg = writer.write_customization(
            customization,
            ConfigLevel.PROJECT,
            fake_home / ".claude",
            project_config,
        )

        assert success is True
        assert "Copied 'test-agent' to Project level" in msg
        target_path = project_config / "agents" / "test-agent.md"
        assert target_path.exists()
        assert target_path.read_text() == "# Test Agent\nAgent content"

    def test_write_skill_copies_entire_directory(
        self, fs, fake_home: Path, fake_project_root: Path
    ) -> None:
        user_config = fake_home / ".claude"
        fs.create_dir(user_config)

        skill_dir = fake_project_root / ".claude" / "skills" / "test-skill"
        fs.create_file(skill_dir / "SKILL.md", contents="# Test Skill")
        fs.create_file(skill_dir / "reference.md", contents="# Reference")
        fs.create_dir(skill_dir / "scripts")
        fs.create_file(skill_dir / "scripts" / "run.py", contents="print('hello')")

        customization = Customization(
            name="test-skill",
            type=CustomizationType.SKILL,
            level=ConfigLevel.PROJECT,
            path=skill_dir / "SKILL.md",
            content="# Test Skill",
        )

        writer = CustomizationWriter()
        success, msg = writer.write_customization(
            customization,
            ConfigLevel.USER,
            user_config,
            fake_project_root / ".claude",
        )

        assert success is True
        assert "Copied 'test-skill' to User level" in msg
        target_dir = user_config / "skills" / "test-skill"
        assert (target_dir / "SKILL.md").exists()
        assert (target_dir / "reference.md").exists()
        assert (target_dir / "scripts" / "run.py").exists()
        assert (target_dir / "scripts" / "run.py").read_text() == "print('hello')"

    def test_conflict_detection_returns_error(
        self, fs, fake_home: Path, fake_project_root: Path
    ) -> None:
        user_config = fake_home / ".claude"
        fs.create_dir(user_config / "commands")
        fs.create_file(user_config / "commands" / "test.md", contents="Existing")

        test_file = fake_project_root / "test.md"
        fs.create_file(test_file, contents="New content")

        customization = Customization(
            name="test",
            type=CustomizationType.SLASH_COMMAND,
            level=ConfigLevel.PROJECT,
            path=test_file,
            content="New content",
        )

        writer = CustomizationWriter()
        success, msg = writer.write_customization(
            customization,
            ConfigLevel.USER,
            user_config,
            fake_project_root / ".claude",
        )

        assert success is False
        assert "already exists at User level" in msg

    def test_creates_parent_directories(
        self, fs, fake_home: Path, fake_project_root: Path
    ) -> None:
        user_config = fake_home / ".claude"
        fs.create_dir(user_config)

        test_file = fake_project_root / "test.md"
        fs.create_file(test_file, contents="# Test")

        customization = Customization(
            name="nested:deep:cmd",
            type=CustomizationType.SLASH_COMMAND,
            level=ConfigLevel.PROJECT,
            path=test_file,
            content="# Test",
        )

        writer = CustomizationWriter()
        success, msg = writer.write_customization(
            customization,
            ConfigLevel.USER,
            user_config,
            fake_project_root / ".claude",
        )

        assert success is True
        target_path = user_config / "commands" / "nested" / "deep" / "cmd.md"
        assert target_path.exists()
        assert target_path.parent.parent.parent == user_config / "commands"

    def test_delete_customization_removes_file(self, fs, fake_home: Path) -> None:
        test_file = fake_home / ".claude" / "commands" / "test.md"
        fs.create_file(test_file, contents="# Test")

        customization = Customization(
            name="test",
            type=CustomizationType.SLASH_COMMAND,
            level=ConfigLevel.USER,
            path=test_file,
            content="# Test",
        )

        writer = CustomizationWriter()
        success, msg = writer.delete_customization(customization)

        assert success is True
        assert "Deleted 'test'" in msg
        assert not test_file.exists()

    def test_delete_skill_removes_directory(self, fs, fake_home: Path) -> None:
        skill_dir = fake_home / ".claude" / "skills" / "test-skill"
        fs.create_file(skill_dir / "SKILL.md", contents="# Test Skill")
        fs.create_file(skill_dir / "reference.md", contents="# Reference")

        customization = Customization(
            name="test-skill",
            type=CustomizationType.SKILL,
            level=ConfigLevel.USER,
            path=skill_dir / "SKILL.md",
            content="# Test Skill",
        )

        writer = CustomizationWriter()
        success, msg = writer.delete_customization(customization)

        assert success is True
        assert "Deleted 'test-skill'" in msg
        assert not skill_dir.exists()

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Permission testing unreliable on Windows with pyfakefs",
    )
    def test_handles_permission_error(
        self, fs, fake_home: Path, fake_project_root: Path
    ) -> None:
        user_config = fake_home / ".claude"
        fs.create_dir(user_config)

        test_file = fake_project_root / "test.md"
        fs.create_file(test_file, contents="# Test")

        customization = Customization(
            name="test",
            type=CustomizationType.SLASH_COMMAND,
            level=ConfigLevel.PROJECT,
            path=test_file,
            content="# Test",
        )

        target_dir = user_config / "commands"
        fs.create_dir(target_dir)

        import os

        os.chmod(str(target_dir), 0o444)

        writer = CustomizationWriter()
        success, msg = writer.write_customization(
            customization,
            ConfigLevel.USER,
            user_config,
            fake_project_root / ".claude",
        )

        assert success is False
        assert "Permission denied" in msg or "Failed to copy" in msg
