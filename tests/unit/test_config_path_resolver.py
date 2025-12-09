"""Tests for ConfigPathResolver service."""

from pathlib import Path
from unittest.mock import Mock

from lazyclaude.models.customization import (
    ConfigLevel,
    Customization,
    CustomizationType,
    PluginInfo,
)
from lazyclaude.services.config_path_resolver import ConfigPathResolver


class TestResolveFile:
    """Tests for resolve_file method."""

    def test_non_plugin_level_returns_path_as_is(self) -> None:
        """Non-plugin customizations return their path unchanged."""
        mock_loader = Mock()
        resolver = ConfigPathResolver(mock_loader)

        customization = Customization(
            name="test",
            type=CustomizationType.SLASH_COMMAND,
            level=ConfigLevel.USER,
            path=Path("/home/user/.claude/commands/test.md"),
            content="test",
        )

        result = resolver.resolve_file(customization)

        assert result == Path("/home/user/.claude/commands/test.md")
        mock_loader.get_plugin_source_path.assert_not_called()

    def test_plugin_without_plugin_info_returns_path_as_is(self) -> None:
        """Plugin customization without plugin_info returns path unchanged."""
        mock_loader = Mock()
        resolver = ConfigPathResolver(mock_loader)

        customization = Customization(
            name="test",
            type=CustomizationType.SLASH_COMMAND,
            level=ConfigLevel.PLUGIN,
            path=Path("/cache/plugin/commands/test.md"),
            content="test",
            plugin_info=None,
        )

        result = resolver.resolve_file(customization)

        assert result == Path("/cache/plugin/commands/test.md")

    def test_plugin_with_directory_source_translates_path(self) -> None:
        """Plugin with directory source translates cached path to source path."""
        mock_loader = Mock()
        mock_loader.get_plugin_source_path.return_value = Path("/dev/my-plugin")
        resolver = ConfigPathResolver(mock_loader)

        plugin_info = PluginInfo(
            plugin_id="test@marketplace",
            short_name="test",
            version="1.0.0",
            install_path=Path("/cache/marketplace/test/1.0.0"),
            is_local=True,
            is_enabled=True,
        )
        customization = Customization(
            name="cmd",
            type=CustomizationType.SLASH_COMMAND,
            level=ConfigLevel.PLUGIN,
            path=Path("/cache/marketplace/test/1.0.0/commands/cmd.md"),
            content="test",
            plugin_info=plugin_info,
        )

        result = resolver.resolve_file(customization)

        assert result == Path("/dev/my-plugin/commands/cmd.md")

    def test_plugin_same_source_and_install_returns_path_as_is(self) -> None:
        """Plugin where source equals install path returns path unchanged."""
        mock_loader = Mock()
        mock_loader.get_plugin_source_path.return_value = Path("/cache/test/1.0.0")
        resolver = ConfigPathResolver(mock_loader)

        plugin_info = PluginInfo(
            plugin_id="test@marketplace",
            short_name="test",
            version="1.0.0",
            install_path=Path("/cache/test/1.0.0"),
            is_local=False,
            is_enabled=True,
        )
        customization = Customization(
            name="cmd",
            type=CustomizationType.SLASH_COMMAND,
            level=ConfigLevel.PLUGIN,
            path=Path("/cache/test/1.0.0/commands/cmd.md"),
            content="test",
            plugin_info=plugin_info,
        )

        result = resolver.resolve_file(customization)

        assert result == Path("/cache/test/1.0.0/commands/cmd.md")

    def test_plugin_source_not_found_returns_path_as_is(self) -> None:
        """Plugin with no source path found returns path unchanged."""
        mock_loader = Mock()
        mock_loader.get_plugin_source_path.return_value = None
        resolver = ConfigPathResolver(mock_loader)

        plugin_info = PluginInfo(
            plugin_id="test@marketplace",
            short_name="test",
            version="1.0.0",
            install_path=Path("/cache/test/1.0.0"),
            is_local=True,
            is_enabled=True,
        )
        customization = Customization(
            name="cmd",
            type=CustomizationType.SLASH_COMMAND,
            level=ConfigLevel.PLUGIN,
            path=Path("/cache/test/1.0.0/commands/cmd.md"),
            content="test",
            plugin_info=plugin_info,
        )

        result = resolver.resolve_file(customization)

        assert result == Path("/cache/test/1.0.0/commands/cmd.md")


class TestResolvePath:
    """Tests for resolve_path method with arbitrary file paths."""

    def test_none_file_path_returns_none(self) -> None:
        """None file_path returns None."""
        mock_loader = Mock()
        resolver = ConfigPathResolver(mock_loader)

        customization = Customization(
            name="test",
            type=CustomizationType.SKILL,
            level=ConfigLevel.USER,
            path=Path("/user/skills/test/SKILL.md"),
            content="test",
        )

        result = resolver.resolve_path(customization, None)

        assert result is None

    def test_resolves_arbitrary_file_within_plugin(self) -> None:
        """Resolves any file path within a plugin's install directory."""
        mock_loader = Mock()
        mock_loader.get_plugin_source_path.return_value = Path("/dev/my-plugin")
        resolver = ConfigPathResolver(mock_loader)

        plugin_info = PluginInfo(
            plugin_id="test@marketplace",
            short_name="test",
            version="1.0.0",
            install_path=Path("/cache/marketplace/test/1.0.0"),
            is_local=True,
            is_enabled=True,
        )
        customization = Customization(
            name="skill",
            type=CustomizationType.SKILL,
            level=ConfigLevel.PLUGIN,
            path=Path("/cache/marketplace/test/1.0.0/skills/my-skill/SKILL.md"),
            content="test",
            plugin_info=plugin_info,
        )

        nested_file = Path(
            "/cache/marketplace/test/1.0.0/skills/my-skill/scripts/run.py"
        )
        result = resolver.resolve_path(customization, nested_file)

        assert result == Path("/dev/my-plugin/skills/my-skill/scripts/run.py")

    def test_file_outside_install_path_returns_unchanged(self) -> None:
        """File path outside plugin install directory returns unchanged."""
        mock_loader = Mock()
        mock_loader.get_plugin_source_path.return_value = Path("/dev/my-plugin")
        resolver = ConfigPathResolver(mock_loader)

        plugin_info = PluginInfo(
            plugin_id="test@marketplace",
            short_name="test",
            version="1.0.0",
            install_path=Path("/cache/marketplace/test/1.0.0"),
            is_local=True,
            is_enabled=True,
        )
        customization = Customization(
            name="cmd",
            type=CustomizationType.SLASH_COMMAND,
            level=ConfigLevel.PLUGIN,
            path=Path("/cache/marketplace/test/1.0.0/commands/cmd.md"),
            content="test",
            plugin_info=plugin_info,
        )

        outside_file = Path("/some/other/path/file.txt")
        result = resolver.resolve_path(customization, outside_file)

        assert result == Path("/some/other/path/file.txt")
