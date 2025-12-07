"""Tests for subagent discovery."""

from pathlib import Path

from lazyclaude.models.customization import ConfigLevel, CustomizationType
from lazyclaude.services.discovery import ConfigDiscoveryService


class TestSubagentDiscovery:
    """Tests for subagent discovery."""

    def test_discovers_user_subagents(
        self, user_config_path: Path, fake_project_root: Path
    ) -> None:
        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=fake_project_root / ".claude",
        )

        subagents = service.discover_by_type(CustomizationType.SUBAGENT)

        user_subagents = [s for s in subagents if s.level == ConfigLevel.USER]
        assert len(user_subagents) == 1
        assert user_subagents[0].name == "explorer"

    def test_subagent_metadata_parsed(
        self, user_config_path: Path, fake_project_root: Path
    ) -> None:
        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=fake_project_root / ".claude",
        )

        subagents = service.discover_by_type(CustomizationType.SUBAGENT)

        explorer = next(s for s in subagents if s.name == "explorer")
        assert explorer.description == "Explores the codebase structure"
        assert explorer.metadata.get("model") == "haiku"
        assert "Glob" in explorer.metadata.get("tools", [])

    def test_discovers_project_subagents(
        self, user_config_path: Path, project_config_path: Path
    ) -> None:
        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=project_config_path,
        )

        subagents = service.discover_by_type(CustomizationType.SUBAGENT)

        project_subagents = [s for s in subagents if s.level == ConfigLevel.PROJECT]
        assert len(project_subagents) == 1
        assert project_subagents[0].name == "reviewer"
        assert project_subagents[0].description == "Reviews code changes"
