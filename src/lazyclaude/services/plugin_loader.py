"""Plugin loading and registry management."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lazyclaude.models.customization import PluginInfo


@dataclass
class PluginRegistry:
    """Container for installed and enabled plugin information."""

    installed: dict[str, dict[str, Any]]
    enabled: dict[str, bool]


class PluginLoader:
    """Loads plugin configuration from the filesystem."""

    def __init__(self, user_config_path: Path) -> None:
        self.user_config_path = user_config_path
        self._registry: PluginRegistry | None = None

    def load_registry(self) -> PluginRegistry:
        """Load installed and enabled plugins from configuration files."""
        if self._registry is not None:
            return self._registry

        installed = self._load_json_dict(
            self.user_config_path / "plugins" / "installed_plugins.json",
            "plugins",
        )
        enabled = self._load_json_dict(
            self.user_config_path / "settings.json",
            "enabledPlugins",
        )

        self._registry = PluginRegistry(installed=installed, enabled=enabled)
        return self._registry

    def get_enabled_plugins(self) -> list[PluginInfo]:
        """Get list of enabled plugin infos with resolved install paths."""
        registry = self.load_registry()
        plugins: list[PluginInfo] = []

        for plugin_id, plugin_data in registry.installed.items():
            if not registry.enabled.get(plugin_id, True):
                continue

            plugin_info = self._create_plugin_info(plugin_id, plugin_data)
            if plugin_info and plugin_info.install_path.is_dir():
                plugins.append(plugin_info)

        return plugins

    def get_all_plugins(self) -> list[PluginInfo]:
        """Get list of ALL plugin infos (enabled and disabled) with resolved install paths."""
        registry = self.load_registry()
        plugins: list[PluginInfo] = []

        for plugin_id, plugin_data in registry.installed.items():
            plugin_info = self._create_plugin_info(plugin_id, plugin_data)
            if plugin_info and plugin_info.install_path.is_dir():
                plugins.append(plugin_info)

        return plugins

    def refresh(self) -> None:
        """Clear cached registry to force reload."""
        self._registry = None

    def _load_json_dict(self, path: Path, key: str) -> dict[str, Any]:
        """Generic JSON dict loader with error handling."""
        if not path.is_file():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            result: dict[str, Any] = data.get(key, {})
            return result
        except (json.JSONDecodeError, OSError):
            return {}

    def _create_plugin_info(
        self, plugin_id: str, plugin_data: dict[str, Any]
    ) -> PluginInfo | None:
        """Create PluginInfo from plugin data."""
        install_path_str = plugin_data.get("installPath")
        if not install_path_str:
            return None

        short_name = plugin_id.split("@")[0] if "@" in plugin_id else plugin_id
        install_path = Path(install_path_str)
        version = plugin_data.get("version", "unknown")

        if not install_path.is_dir() and install_path.parent.is_dir():
            install_path = self._find_latest_version_dir(install_path.parent)
            version = install_path.name

        is_enabled = True
        if self._registry:
            is_enabled = self._registry.enabled.get(plugin_id, True)

        return PluginInfo(
            plugin_id=plugin_id,
            short_name=short_name,
            version=version,
            install_path=install_path,
            is_local=plugin_data.get("isLocal", False),
            is_enabled=is_enabled,
        )

    def _find_latest_version_dir(self, parent_dir: Path) -> Path:
        """Find the latest version directory in a plugin parent directory.

        Uses semantic version comparison (e.g., "10.0.0" > "2.0.0").
        Falls back to string comparison for non-semver directory names.
        """
        try:
            subdirs = [d for d in parent_dir.iterdir() if d.is_dir()]
            if subdirs:
                return max(subdirs, key=lambda d: self._parse_version(d.name))
        except OSError:
            pass
        return parent_dir

    @staticmethod
    def _parse_version(version_str: str) -> tuple[int, ...] | tuple[str]:
        """Parse version string into comparable tuple.

        Returns tuple of ints for semver (e.g., "1.2.3" -> (1, 2, 3)).
        Returns tuple with original string for non-semver names.
        """
        try:
            return tuple(int(part) for part in version_str.split("."))
        except ValueError:
            return (version_str,)
