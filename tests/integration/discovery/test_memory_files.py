"""Tests for memory file discovery."""

from pathlib import Path

from lazyclaude.models.customization import ConfigLevel, CustomizationType
from lazyclaude.services.discovery import ConfigDiscoveryService


class TestMemoryFileDiscovery:
    """Tests for memory file discovery."""

    def test_discovers_user_memory_files(
        self, user_config_path: Path, fake_project_root: Path
    ) -> None:
        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=fake_project_root / ".claude",
        )

        memory_files = service.discover_by_type(CustomizationType.MEMORY_FILE)

        user_memory = [m for m in memory_files if m.level == ConfigLevel.USER]
        assert len(user_memory) == 2
        names = {m.name for m in user_memory}
        assert "CLAUDE.md" in names
        assert "AGENTS.md" in names

    def test_memory_file_content_available(
        self, user_config_path: Path, fake_project_root: Path
    ) -> None:
        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=fake_project_root / ".claude",
        )

        memory_files = service.discover_by_type(CustomizationType.MEMORY_FILE)

        claude_md = next(m for m in memory_files if m.name == "CLAUDE.md")
        assert claude_md.content is not None
        assert "Project Guidelines" in claude_md.content

    def test_discovers_project_memory_files(
        self, user_config_path: Path, project_config_path: Path
    ) -> None:
        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=project_config_path,
        )

        memory_files = service.discover_by_type(CustomizationType.MEMORY_FILE)

        project_memory = [m for m in memory_files if m.level == ConfigLevel.PROJECT]
        assert len(project_memory) == 1
        assert project_memory[0].name == "CLAUDE.md"
        assert "Build Commands" in project_memory[0].content
