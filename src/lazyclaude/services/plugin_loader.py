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

        if install_path.parent.is_dir():
            short_name_path = install_path.parent / short_name
            if short_name_path.is_dir() and (
                short_name_path != install_path or not install_path.is_dir()
            ):
                install_path = short_name_path

        return PluginInfo(
            plugin_id=plugin_id,
            short_name=short_name,
            version=plugin_data.get("version", "unknown"),
            install_path=install_path,
            is_local=plugin_data.get("isLocal", False),
        )
