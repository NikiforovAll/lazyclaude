"""Tests for PluginLoader plugin source path resolution."""

import json
from pathlib import Path

from pyfakefs.fake_filesystem import FakeFilesystem

from lazyclaude.services.plugin_loader import PluginLoader


class TestGetPluginSourcePath:
    """Tests for get_plugin_source_path method."""

    def test_directory_source_resolves_to_plugin_path(self, fs: FakeFilesystem) -> None:
        """Directory source plugin resolves to actual plugin source path."""
        user_config = Path("/home/user/.claude")
        fs.create_dir(user_config / "plugins")

        fs.create_file(
            user_config / "plugins" / "known_marketplaces.json",
            contents=json.dumps(
                {
                    "my-marketplace": {
                        "source": {"source": "directory", "path": "/dev/my-marketplace"}
                    }
                }
            ),
        )

        fs.create_file(
            user_config / "plugins" / "installed_plugins_v2.json",
            contents=json.dumps(
                {
                    "version": 2,
                    "plugins": {
                        "handbook@my-marketplace": [
                            {
                                "scope": "user",
                                "version": "1.0.0",
                                "installPath": "/home/user/.claude/plugins/cache/my-marketplace/handbook/1.0.0",
                            }
                        ]
                    },
                }
            ),
        )

        marketplace_json = Path("/dev/my-marketplace/.claude-plugin/marketplace.json")
        fs.create_file(
            marketplace_json,
            contents=json.dumps(
                {
                    "name": "my-marketplace",
                    "plugins": [{"name": "handbook", "source": "./plugins/handbook"}],
                }
            ),
        )

        fs.create_dir("/dev/my-marketplace/plugins/handbook")

        loader = PluginLoader(user_config)
        result = loader.get_plugin_source_path("handbook@my-marketplace")

        assert result is not None
        assert result.parts[-3:] == ("my-marketplace", "plugins", "handbook")

    def test_non_directory_source_returns_install_path(
        self, fs: FakeFilesystem
    ) -> None:
        """Non-directory source plugin returns install path."""
        user_config = Path("/home/user/.claude")
        fs.create_dir(user_config / "plugins")

        fs.create_file(
            user_config / "plugins" / "known_marketplaces.json",
            contents=json.dumps(
                {
                    "remote-marketplace": {
                        "source": {
                            "source": "git",
                            "url": "https://github.com/example/plugins",
                        }
                    }
                }
            ),
        )

        install_path = "/home/user/.claude/plugins/cache/remote/plugin/1.0.0"
        fs.create_file(
            user_config / "plugins" / "installed_plugins_v2.json",
            contents=json.dumps(
                {
                    "version": 2,
                    "plugins": {
                        "plugin@remote-marketplace": [
                            {
                                "scope": "user",
                                "version": "1.0.0",
                                "installPath": install_path,
                            }
                        ]
                    },
                }
            ),
        )

        loader = PluginLoader(user_config)
        result = loader.get_plugin_source_path("plugin@remote-marketplace")

        assert result == Path(install_path)

    def test_missing_marketplace_json_returns_marketplace_root(
        self, fs: FakeFilesystem
    ) -> None:
        """Missing marketplace.json returns marketplace root directory."""
        user_config = Path("/home/user/.claude")
        fs.create_dir(user_config / "plugins")

        fs.create_file(
            user_config / "plugins" / "known_marketplaces.json",
            contents=json.dumps(
                {
                    "local": {
                        "source": {"source": "directory", "path": "/dev/local-plugins"}
                    }
                }
            ),
        )

        fs.create_file(
            user_config / "plugins" / "installed_plugins_v2.json",
            contents=json.dumps(
                {
                    "version": 2,
                    "plugins": {
                        "test@local": [
                            {
                                "scope": "user",
                                "version": "1.0.0",
                                "installPath": "/cache/local/test/1.0.0",
                            }
                        ]
                    },
                }
            ),
        )

        fs.create_dir("/dev/local-plugins")

        loader = PluginLoader(user_config)
        result = loader.get_plugin_source_path("test@local")

        assert result == Path("/dev/local-plugins")

    def test_plugin_not_in_marketplace_json_returns_root(
        self, fs: FakeFilesystem
    ) -> None:
        """Plugin not found in marketplace.json returns marketplace root."""
        user_config = Path("/home/user/.claude")
        fs.create_dir(user_config / "plugins")

        fs.create_file(
            user_config / "plugins" / "known_marketplaces.json",
            contents=json.dumps(
                {
                    "local": {
                        "source": {"source": "directory", "path": "/dev/local-plugins"}
                    }
                }
            ),
        )

        fs.create_file(
            user_config / "plugins" / "installed_plugins_v2.json",
            contents=json.dumps(
                {
                    "version": 2,
                    "plugins": {
                        "missing@local": [
                            {
                                "scope": "user",
                                "version": "1.0.0",
                                "installPath": "/cache/local/missing/1.0.0",
                            }
                        ]
                    },
                }
            ),
        )

        fs.create_file(
            "/dev/local-plugins/.claude-plugin/marketplace.json",
            contents=json.dumps(
                {
                    "name": "local",
                    "plugins": [{"name": "other-plugin", "source": "./plugins/other"}],
                }
            ),
        )

        loader = PluginLoader(user_config)
        result = loader.get_plugin_source_path("missing@local")

        assert result == Path("/dev/local-plugins")

    def test_plugin_without_marketplace_returns_install_path(
        self, fs: FakeFilesystem
    ) -> None:
        """Plugin ID without @ returns install path from registry."""
        user_config = Path("/home/user/.claude")
        fs.create_dir(user_config / "plugins")

        fs.create_file(
            user_config / "plugins" / "known_marketplaces.json",
            contents="{}",
        )

        install_path = "/home/user/.claude/plugins/standalone/1.0.0"
        fs.create_file(
            user_config / "plugins" / "installed_plugins_v2.json",
            contents=json.dumps(
                {
                    "version": 2,
                    "plugins": {
                        "standalone": [
                            {
                                "scope": "user",
                                "version": "1.0.0",
                                "installPath": install_path,
                            }
                        ]
                    },
                }
            ),
        )

        loader = PluginLoader(user_config)
        result = loader.get_plugin_source_path("standalone")

        assert result == Path(install_path)

    def test_unknown_plugin_returns_none(self, fs: FakeFilesystem) -> None:
        """Unknown plugin ID returns None."""
        user_config = Path("/home/user/.claude")
        fs.create_dir(user_config / "plugins")

        fs.create_file(
            user_config / "plugins" / "known_marketplaces.json",
            contents="{}",
        )

        fs.create_file(
            user_config / "plugins" / "installed_plugins_v2.json",
            contents=json.dumps({"version": 2, "plugins": {}}),
        )

        loader = PluginLoader(user_config)
        result = loader.get_plugin_source_path("nonexistent@unknown")

        assert result is None

    def test_malformed_marketplace_json_returns_root(self, fs: FakeFilesystem) -> None:
        """Malformed marketplace.json returns marketplace root."""
        user_config = Path("/home/user/.claude")
        fs.create_dir(user_config / "plugins")

        fs.create_file(
            user_config / "plugins" / "known_marketplaces.json",
            contents=json.dumps(
                {"local": {"source": {"source": "directory", "path": "/dev/local"}}}
            ),
        )

        fs.create_file(
            user_config / "plugins" / "installed_plugins_v2.json",
            contents=json.dumps(
                {
                    "version": 2,
                    "plugins": {
                        "test@local": [
                            {
                                "scope": "user",
                                "version": "1.0.0",
                                "installPath": "/cache/test",
                            }
                        ]
                    },
                }
            ),
        )

        fs.create_file(
            "/dev/local/.claude-plugin/marketplace.json",
            contents="{ invalid json }",
        )

        loader = PluginLoader(user_config)
        result = loader.get_plugin_source_path("test@local")

        assert result == Path("/dev/local")
