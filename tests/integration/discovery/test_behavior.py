"""Tests for discovery service behavior (caching, edge cases, path resolution, multi-level)."""

from pathlib import Path

from pyfakefs.fake_filesystem import FakeFilesystem

from lazyclaude.models.customization import ConfigLevel, CustomizationType
from lazyclaude.services.discovery import ConfigDiscoveryService


class TestMultiLevelDiscovery:
    """Tests for discover_all and discover_by_level."""

    def test_discover_all_returns_sorted_results(
        self,
        full_user_config: Path,
        full_project_config: Path,
    ) -> None:
        service = ConfigDiscoveryService(
            user_config_path=full_user_config,
            project_config_path=full_project_config,
        )

        all_customizations = service.discover_all()

        assert len(all_customizations) > 0

        types_seen = [c.type for c in all_customizations]
        type_order = list(CustomizationType)
        for i in range(len(types_seen) - 1):
            curr_idx = type_order.index(types_seen[i])
            next_idx = type_order.index(types_seen[i + 1])
            assert curr_idx <= next_idx, "Results should be sorted by type"

    def test_discover_by_level_user(
        self, full_user_config: Path, fake_project_root: Path
    ) -> None:
        service = ConfigDiscoveryService(
            user_config_path=full_user_config,
            project_config_path=fake_project_root / ".claude",
        )

        user_items = service.discover_by_level(ConfigLevel.USER)

        assert len(user_items) > 0
        assert all(c.level == ConfigLevel.USER for c in user_items)

    def test_discover_by_level_project(
        self, user_config_path: Path, full_project_config: Path
    ) -> None:
        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=full_project_config,
        )

        project_items = service.discover_by_level(ConfigLevel.PROJECT)

        assert len(project_items) > 0
        assert all(c.level == ConfigLevel.PROJECT for c in project_items)

    def test_discover_by_level_plugin(
        self,
        full_user_config: Path,
        fake_project_root: Path,
    ) -> None:
        service = ConfigDiscoveryService(
            user_config_path=full_user_config,
            project_config_path=fake_project_root / ".claude",
        )

        plugin_items = service.discover_by_level(ConfigLevel.PLUGIN)

        assert len(plugin_items) > 0
        assert all(c.level == ConfigLevel.PLUGIN for c in plugin_items)


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_directories_returns_empty(self, fs: FakeFilesystem) -> None:
        user_config = Path("/empty/user/.claude")
        project_config = Path("/empty/project/.claude")
        fs.create_dir(user_config)
        fs.create_dir(project_config)

        service = ConfigDiscoveryService(
            user_config_path=user_config,
            project_config_path=project_config,
        )

        all_items = service.discover_all()

        assert all_items == []

    def test_missing_directories_handled_gracefully(
        self,
        fs: FakeFilesystem,  # noqa: ARG002
    ) -> None:
        user_config = Path("/nonexistent/user/.claude")
        project_config = Path("/nonexistent/project/.claude")

        service = ConfigDiscoveryService(
            user_config_path=user_config,
            project_config_path=project_config,
        )

        all_items = service.discover_all()

        assert all_items == []

    def test_malformed_json_sets_error(self, fs: FakeFilesystem) -> None:
        user_config = Path("/test/user/.claude")
        project_config = Path("/test/project/.claude")
        project_root = Path("/test/project")
        fs.create_dir(user_config)
        fs.create_dir(project_config)
        fs.create_file(
            project_root / ".mcp.json",
            contents="{ invalid json }",
        )

        service = ConfigDiscoveryService(
            user_config_path=user_config,
            project_config_path=project_config,
        )

        mcps = service.discover_by_type(CustomizationType.MCP)

        assert len(mcps) == 1
        assert mcps[0].has_error
        assert "parse" in mcps[0].error.lower()

    def test_malformed_yaml_frontmatter_falls_back_gracefully(
        self, fs: FakeFilesystem
    ) -> None:
        """Parser is lenient: malformed YAML frontmatter treated as no frontmatter."""
        user_config = Path("/test/user/.claude")
        project_config = Path("/test/project/.claude")
        fs.create_dir(user_config)
        fs.create_dir(project_config / "commands")
        fs.create_file(
            project_config / "commands" / "bad.md",
            contents="---\n[unclosed bracket\n---\n# Bad",
        )

        service = ConfigDiscoveryService(
            user_config_path=user_config,
            project_config_path=project_config,
        )

        commands = service.discover_by_type(CustomizationType.SLASH_COMMAND)

        bad_cmd = next((c for c in commands if c.name == "bad"), None)
        assert bad_cmd is not None
        assert not bad_cmd.has_error
        assert bad_cmd.metadata.get("allowed_tools") == []


class TestCachingAndRefresh:
    """Tests for caching behavior and refresh."""

    def test_discover_all_caches_results(
        self, user_config_path: Path, fake_project_root: Path
    ) -> None:
        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=fake_project_root / ".claude",
        )

        first_call = service.discover_all()
        second_call = service.discover_all()

        assert first_call is second_call

    def test_refresh_clears_cache(
        self, user_config_path: Path, fake_project_root: Path, fs: FakeFilesystem
    ) -> None:
        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=fake_project_root / ".claude",
        )

        first_call = service.discover_all()
        first_count = len(first_call)

        fs.create_file(
            user_config_path / "commands" / "new-cmd.md",
            contents="---\ndescription: New command\n---\n# New",
        )

        refreshed = service.refresh()

        assert len(refreshed) == first_count + 1
        assert refreshed is not first_call


class TestPathResolution:
    """Tests for get_active_config_path."""

    def test_returns_project_path_when_exists(
        self, user_config_path: Path, project_config_path: Path
    ) -> None:
        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=project_config_path,
        )

        active_path = service.get_active_config_path()

        assert active_path == project_config_path.resolve()

    def test_returns_user_path_when_project_missing(
        self,
        user_config_path: Path,
        fs: FakeFilesystem,  # noqa: ARG002
    ) -> None:
        nonexistent_project = Path("/nonexistent/project/.claude")

        service = ConfigDiscoveryService(
            user_config_path=user_config_path,
            project_config_path=nonexistent_project,
        )

        active_path = service.get_active_config_path()

        assert active_path == user_config_path
