"""Tests for plugin discovery."""

from pathlib import Path

from pyfakefs.fake_filesystem import FakeFilesystem

from lazyclaude.models.customization import ConfigLevel, CustomizationType
from lazyclaude.services.discovery import ConfigDiscoveryService


class TestPluginDiscovery:
    """Tests for plugin discovery."""

    def test_discovers_enabled_plugin_commands(
        self,
        full_user_config: Path,
        fake_project_root: Path,
    ) -> None:
        service = ConfigDiscoveryService(
            user_config_path=full_user_config,
            project_config_path=fake_project_root / ".claude",
        )

        commands = service.discover_by_type(CustomizationType.SLASH_COMMAND)

        plugin_commands = [c for c in commands if c.level == ConfigLevel.PLUGIN]
        assert len(plugin_commands) >= 1
        plugin_cmd = next((c for c in plugin_commands if c.name == "plugin-cmd"), None)
        assert plugin_cmd is not None
        assert plugin_cmd.plugin_info is not None
        assert plugin_cmd.plugin_info.plugin_id == "example-plugin@test"

    def test_disabled_plugins_included(
        self,
        full_user_config: Path,
        fake_project_root: Path,
        fs: FakeFilesystem,
    ) -> None:
        """Test that disabled plugins are still discovered but marked as disabled."""
        # V2 uses versioned cache paths
        disabled_plugin_dir = Path(
            "/fake/home/.claude/plugins/cache/test/disabled-plugin/1.0.0"
        )
        fs.create_dir(disabled_plugin_dir / "commands")
        fs.create_file(
            disabled_plugin_dir / "commands" / "disabled-cmd.md",
            contents="---\ndescription: Should appear but marked as disabled\n---\n# Disabled",
        )

        service = ConfigDiscoveryService(
            user_config_path=full_user_config,
            project_config_path=fake_project_root / ".claude",
        )

        commands = service.discover_by_type(CustomizationType.SLASH_COMMAND)

        disabled_cmds = [c for c in commands if "disabled-cmd" in c.name]
        assert len(disabled_cmds) == 1
        assert disabled_cmds[0].plugin_info is not None
        assert disabled_cmds[0].plugin_info.is_enabled is False

    def test_plugin_subagents_discovered(
        self,
        full_user_config: Path,
        fake_project_root: Path,
    ) -> None:
        service = ConfigDiscoveryService(
            user_config_path=full_user_config,
            project_config_path=fake_project_root / ".claude",
        )

        subagents = service.discover_by_type(CustomizationType.SUBAGENT)

        plugin_agents = [s for s in subagents if s.level == ConfigLevel.PLUGIN]
        assert len(plugin_agents) >= 1
        plugin_agent = next(
            (s for s in plugin_agents if s.name == "plugin-agent"), None
        )
        assert plugin_agent is not None

    def test_plugin_skills_discovered(
        self,
        full_user_config: Path,
        fake_project_root: Path,
    ) -> None:
        service = ConfigDiscoveryService(
            user_config_path=full_user_config,
            project_config_path=fake_project_root / ".claude",
        )

        skills = service.discover_by_type(CustomizationType.SKILL)

        plugin_skills = [s for s in skills if s.level == ConfigLevel.PLUGIN]
        assert len(plugin_skills) >= 1
