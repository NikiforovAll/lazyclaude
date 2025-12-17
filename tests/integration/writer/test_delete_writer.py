"""Tests for delete functionality in CustomizationWriter."""

from pathlib import Path

from pyfakefs.fake_filesystem import FakeFilesystem

from lazyclaude.models.customization import (
    ConfigLevel,
    Customization,
    CustomizationType,
)
from lazyclaude.services.writer import CustomizationWriter


def _create_customization(
    name: str,
    ctype: CustomizationType,
    level: ConfigLevel,
    path: Path,
) -> Customization:
    """Create a customization for testing."""
    return Customization(
        name=name,
        type=ctype,
        level=level,
        path=path,
        description=f"Test {ctype.value} {name}",
        content="Test content",
    )


class TestDeleteSlashCommand:
    """Tests for deleting slash commands."""

    def test_delete_slash_command_removes_file(
        self,
        fake_home: Path,
        fs: FakeFilesystem,
    ) -> None:
        """Deleting slash command removes the .md file."""
        user_claude = fake_home / ".claude"
        fs.create_dir(user_claude / "commands")
        cmd_path = user_claude / "commands" / "test-cmd.md"
        fs.create_file(cmd_path, contents="# Test command")

        customization = _create_customization(
            "test-cmd",
            CustomizationType.SLASH_COMMAND,
            ConfigLevel.USER,
            cmd_path,
        )
        writer = CustomizationWriter()

        success, msg = writer.delete_customization(customization)

        assert success is True
        assert "Deleted" in msg
        assert not cmd_path.exists()

    def test_delete_nested_slash_command_removes_file(
        self,
        fake_home: Path,
        fs: FakeFilesystem,
    ) -> None:
        """Deleting nested slash command removes the file but preserves parent dir."""
        user_claude = fake_home / ".claude"
        nested_dir = user_claude / "commands" / "nested"
        fs.create_dir(nested_dir)
        cmd_path = nested_dir / "sub-cmd.md"
        fs.create_file(cmd_path, contents="# Nested command")
        other_file = nested_dir / "other.md"
        fs.create_file(other_file, contents="# Other")

        customization = _create_customization(
            "nested:sub-cmd",
            CustomizationType.SLASH_COMMAND,
            ConfigLevel.USER,
            cmd_path,
        )
        writer = CustomizationWriter()

        success, _ = writer.delete_customization(customization)

        assert success is True
        assert not cmd_path.exists()
        assert nested_dir.exists()
        assert other_file.exists()

    def test_delete_slash_command_nonexistent_fails(
        self,
        fake_home: Path,
        fs: FakeFilesystem,
    ) -> None:
        """Deleting non-existent slash command returns error."""
        user_claude = fake_home / ".claude"
        fs.create_dir(user_claude / "commands")
        cmd_path = user_claude / "commands" / "missing.md"

        customization = _create_customization(
            "missing",
            CustomizationType.SLASH_COMMAND,
            ConfigLevel.USER,
            cmd_path,
        )
        writer = CustomizationWriter()

        success, msg = writer.delete_customization(customization)

        assert success is False
        assert "Failed to delete" in msg


class TestDeleteSubagent:
    """Tests for deleting subagents."""

    def test_delete_subagent_removes_file(
        self,
        fake_home: Path,
        fs: FakeFilesystem,
    ) -> None:
        """Deleting subagent removes the .md file."""
        user_claude = fake_home / ".claude"
        fs.create_dir(user_claude / "agents")
        agent_path = user_claude / "agents" / "test-agent.md"
        fs.create_file(agent_path, contents="# Test agent")

        customization = _create_customization(
            "test-agent",
            CustomizationType.SUBAGENT,
            ConfigLevel.USER,
            agent_path,
        )
        writer = CustomizationWriter()

        success, msg = writer.delete_customization(customization)

        assert success is True
        assert "Deleted" in msg
        assert not agent_path.exists()

    def test_delete_subagent_preserves_sibling_files(
        self,
        fake_home: Path,
        fs: FakeFilesystem,
    ) -> None:
        """Deleting subagent preserves other agents in the directory."""
        user_claude = fake_home / ".claude"
        agents_dir = user_claude / "agents"
        fs.create_dir(agents_dir)
        agent_path = agents_dir / "delete-me.md"
        fs.create_file(agent_path, contents="# Delete me")
        other_agent = agents_dir / "keep-me.md"
        fs.create_file(other_agent, contents="# Keep me")

        customization = _create_customization(
            "delete-me",
            CustomizationType.SUBAGENT,
            ConfigLevel.USER,
            agent_path,
        )
        writer = CustomizationWriter()

        success, _ = writer.delete_customization(customization)

        assert success is True
        assert not agent_path.exists()
        assert other_agent.exists()


class TestDeleteSkill:
    """Tests for deleting skills."""

    def test_delete_skill_removes_entire_directory(
        self,
        fake_home: Path,
        fs: FakeFilesystem,
    ) -> None:
        """Deleting skill removes the entire skill directory."""
        user_claude = fake_home / ".claude"
        skill_dir = user_claude / "skills" / "test-skill"
        fs.create_dir(skill_dir)
        skill_md = skill_dir / "SKILL.md"
        fs.create_file(skill_md, contents="# Test skill")
        helper_file = skill_dir / "helper.py"
        fs.create_file(helper_file, contents="# Helper")

        customization = _create_customization(
            "test-skill",
            CustomizationType.SKILL,
            ConfigLevel.USER,
            skill_md,
        )
        writer = CustomizationWriter()

        success, msg = writer.delete_customization(customization)

        assert success is True
        assert "Deleted" in msg
        assert not skill_dir.exists()
        assert not skill_md.exists()
        assert not helper_file.exists()

    def test_delete_skill_preserves_sibling_skills(
        self,
        fake_home: Path,
        fs: FakeFilesystem,
    ) -> None:
        """Deleting skill preserves other skills in the directory."""
        user_claude = fake_home / ".claude"
        skills_dir = user_claude / "skills"

        skill_to_delete = skills_dir / "delete-skill"
        fs.create_dir(skill_to_delete)
        fs.create_file(skill_to_delete / "SKILL.md", contents="# Delete")

        skill_to_keep = skills_dir / "keep-skill"
        fs.create_dir(skill_to_keep)
        fs.create_file(skill_to_keep / "SKILL.md", contents="# Keep")

        customization = _create_customization(
            "delete-skill",
            CustomizationType.SKILL,
            ConfigLevel.USER,
            skill_to_delete / "SKILL.md",
        )
        writer = CustomizationWriter()

        success, _ = writer.delete_customization(customization)

        assert success is True
        assert not skill_to_delete.exists()
        assert skill_to_keep.exists()
        assert (skill_to_keep / "SKILL.md").exists()


class TestDeleteMemoryFile:
    """Tests for deleting memory files."""

    def test_delete_memory_file_removes_file(
        self,
        fake_home: Path,
        fs: FakeFilesystem,
    ) -> None:
        """Deleting memory file removes the file."""
        user_claude = fake_home / ".claude"
        fs.create_dir(user_claude)
        memory_path = user_claude / "CLAUDE.md"
        fs.create_file(memory_path, contents="# Memory file")

        customization = _create_customization(
            "CLAUDE.md",
            CustomizationType.MEMORY_FILE,
            ConfigLevel.USER,
            memory_path,
        )
        writer = CustomizationWriter()

        success, msg = writer.delete_customization(customization)

        assert success is True
        assert "Deleted" in msg
        assert not memory_path.exists()

    def test_delete_memory_file_preserves_other_files(
        self,
        fake_home: Path,
        fs: FakeFilesystem,
    ) -> None:
        """Deleting memory file preserves other memory files."""
        user_claude = fake_home / ".claude"
        fs.create_dir(user_claude)
        delete_path = user_claude / "AGENTS.md"
        fs.create_file(delete_path, contents="# Delete")
        keep_path = user_claude / "CLAUDE.md"
        fs.create_file(keep_path, contents="# Keep")

        customization = _create_customization(
            "AGENTS.md",
            CustomizationType.MEMORY_FILE,
            ConfigLevel.USER,
            delete_path,
        )
        writer = CustomizationWriter()

        success, _ = writer.delete_customization(customization)

        assert success is True
        assert not delete_path.exists()
        assert keep_path.exists()


class TestDeleteFromProjectLevel:
    """Tests for deleting from project level."""

    def test_delete_slash_command_from_project(
        self,
        fake_project_root: Path,
        fs: FakeFilesystem,
    ) -> None:
        """Deleting slash command from project level works."""
        project_claude = fake_project_root / ".claude"
        fs.create_dir(project_claude / "commands")
        cmd_path = project_claude / "commands" / "project-cmd.md"
        fs.create_file(cmd_path, contents="# Project command")

        customization = _create_customization(
            "project-cmd",
            CustomizationType.SLASH_COMMAND,
            ConfigLevel.PROJECT,
            cmd_path,
        )
        writer = CustomizationWriter()

        success, msg = writer.delete_customization(customization)

        assert success is True
        assert "Deleted" in msg
        assert not cmd_path.exists()

    def test_delete_skill_from_project(
        self,
        fake_project_root: Path,
        fs: FakeFilesystem,
    ) -> None:
        """Deleting skill from project level removes directory."""
        project_claude = fake_project_root / ".claude"
        skill_dir = project_claude / "skills" / "project-skill"
        fs.create_dir(skill_dir)
        skill_md = skill_dir / "SKILL.md"
        fs.create_file(skill_md, contents="# Project skill")

        customization = _create_customization(
            "project-skill",
            CustomizationType.SKILL,
            ConfigLevel.PROJECT,
            skill_md,
        )
        writer = CustomizationWriter()

        success, _ = writer.delete_customization(customization)

        assert success is True
        assert not skill_dir.exists()
