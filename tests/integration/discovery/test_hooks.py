"""Tests for hook discovery."""

from pathlib import Path

from lazyclaude.models.customization import ConfigLevel, CustomizationType
from lazyclaude.services.discovery import ConfigDiscoveryService


class TestHookDiscovery:
    """Tests for hook discovery."""

    def test_discovers_user_hooks(
        self, user_config_path: Path, fake_project_root: Path
    ) -> None:
        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=fake_project_root / ".claude",
        )

        hooks = service.discover_by_type(CustomizationType.HOOK)

        user_hooks = [h for h in hooks if h.level == ConfigLevel.USER]
        assert len(user_hooks) >= 1

    def test_discovers_project_hooks(
        self,
        user_config_path: Path,
        project_config_path: Path,
    ) -> None:
        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=project_config_path,
        )

        hooks = service.discover_by_type(CustomizationType.HOOK)

        project_hooks = [h for h in hooks if h.level == ConfigLevel.PROJECT]
        assert len(project_hooks) >= 1
