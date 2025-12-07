"""Tests for slash command discovery."""

from pathlib import Path

from lazyclaude.models.customization import ConfigLevel, CustomizationType
from lazyclaude.services.discovery import ConfigDiscoveryService


class TestSlashCommandDiscovery:
    """Tests for slash command discovery."""

    def test_discovers_user_slash_commands(
        self, user_config_path: Path, fake_project_root: Path
    ) -> None:
        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=fake_project_root / ".claude",
        )

        commands = service.discover_by_type(CustomizationType.SLASH_COMMAND)

        user_commands = [c for c in commands if c.level == ConfigLevel.USER]
        assert len(user_commands) == 2
        names = {c.name for c in user_commands}
        assert "greet" in names
        assert "nested:deep-cmd" in names

    def test_discovers_project_slash_commands(
        self, user_config_path: Path, project_config_path: Path
    ) -> None:
        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=project_config_path,
        )

        commands = service.discover_by_type(CustomizationType.SLASH_COMMAND)

        project_commands = [c for c in commands if c.level == ConfigLevel.PROJECT]
        assert len(project_commands) == 1
        assert project_commands[0].name == "project-cmd"

    def test_slash_command_metadata_parsed(
        self, user_config_path: Path, fake_project_root: Path
    ) -> None:
        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=fake_project_root / ".claude",
        )

        commands = service.discover_by_type(CustomizationType.SLASH_COMMAND)

        greet = next(c for c in commands if c.name == "greet")
        assert greet.description == "Say hello to someone"
        assert greet.metadata.get("allowed_tools") == ["Bash(echo:*)"]
        assert greet.metadata.get("argument_hint") == "<name>"
