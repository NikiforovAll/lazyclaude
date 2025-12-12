"""Plugin loading and registry management."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lazyclaude.models.customization import PluginInfo, PluginScope


@dataclass
class PluginInstallation:
    """Single installation of a plugin (user or project-scoped)."""

    scope: str
    install_path: str
    version: str
    is_local: bool = False
    project_path: str | None = None


@dataclass
class PluginRegistry:
    """Container for installed and enabled plugin information."""

    installed: dict[str, list[PluginInstallation]]
    user_enabled: dict[str, bool]
    project_enabled: dict[str, bool]
    local_enabled: dict[str, bool]


class PluginLoader:
    """Loads plugin configuration from the filesystem."""

    def __init__(
        self,
        user_config_path: Path,
        project_config_path: Path | None = None,
        project_root: Path | None = None,
    ) -> None:
        self.user_config_path = user_config_path
        self.project_config_path = project_config_path
        self.project_root = project_root
        self._registry: PluginRegistry | None = None

    def load_registry(self) -> PluginRegistry:
        """Load installed and enabled plugins from configuration files."""
        if self._registry is not None:
            return self._registry

        v2_file = self.user_config_path / "plugins" / "installed_plugins.json"
        installed = self._load_v2_plugins(v2_file) if v2_file.is_file() else {}

        user_enabled = self._load_json_dict(
            self.user_config_path / "settings.json",
            "enabledPlugins",
        )

        project_enabled: dict[str, bool] = {}
        local_enabled: dict[str, bool] = {}
        if self.project_config_path:
            project_enabled = self._load_json_dict(
                self.project_config_path / "settings.json",
                "enabledPlugins",
            )
            local_enabled = self._load_json_dict(
                self.project_config_path / "settings.local.json",
                "enabledPlugins",
            )

        self._registry = PluginRegistry(
            installed=installed,
            user_enabled=user_enabled,
            project_enabled=project_enabled,
            local_enabled=local_enabled,
        )
        return self._registry

    def _load_v2_plugins(self, path: Path) -> dict[str, list[PluginInstallation]]:
        """Parse V2 format where plugins value is a list."""
        if not path.is_file():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            plugins_data = data.get("plugins", {})
            result: dict[str, list[PluginInstallation]] = {}

            for plugin_id, installations in plugins_data.items():
                result[plugin_id] = [
                    PluginInstallation(
                        scope=inst.get("scope", "user"),
                        install_path=inst.get("installPath", ""),
                        version=inst.get("version", "unknown"),
                        is_local=inst.get("isLocal", False),
                        project_path=inst.get("projectPath"),
                    )
                    for inst in installations
                ]
            return result
        except (json.JSONDecodeError, OSError):
            return {}

    def get_enabled_plugins(self) -> list[PluginInfo]:
        """Get list of enabled plugin infos with resolved install paths."""
        all_plugins = self.get_all_plugins()
        return [p for p in all_plugins if p.is_enabled]

    def get_all_plugins(self) -> list[PluginInfo]:
        """Get list of ALL plugin infos (enabled and disabled) with resolved install paths.

        Uses three-phase discovery:
        1. User plugins: All entries with scope="user"
        2. Project plugins: Entries from project's settings.json enabledPlugins
           that have scope="project" and matching projectPath
        3. Local plugins: Entries from project's settings.local.json enabledPlugins
           that have scope="local" and matching projectPath
        """
        registry = self.load_registry()
        plugins: list[PluginInfo] = []

        # Phase 1: User-scoped plugins
        for plugin_id, installations in registry.installed.items():
            for installation in installations:
                if installation.scope == "user":
                    plugin_info = self._create_plugin_info(
                        plugin_id, installation, scope_type="user"
                    )
                    if plugin_info and plugin_info.install_path.is_dir():
                        plugins.append(plugin_info)

        # Phase 2: Project-scoped plugins (driven by project settings.json)
        for plugin_id in registry.project_enabled:
            installations = registry.installed.get(plugin_id, [])
            for installation in installations:
                if installation.scope == "project" and self._matches_current_project(
                    installation.project_path
                ):
                    plugin_info = self._create_plugin_info(
                        plugin_id, installation, scope_type="project"
                    )
                    if plugin_info and plugin_info.install_path.is_dir():
                        plugins.append(plugin_info)

        # Phase 3: Local-scoped plugins (driven by settings.local.json)
        for plugin_id in registry.local_enabled:
            installations = registry.installed.get(plugin_id, [])
            for installation in installations:
                if installation.scope == "local" and self._matches_current_project(
                    installation.project_path
                ):
                    plugin_info = self._create_plugin_info(
                        plugin_id, installation, scope_type="local"
                    )
                    if plugin_info and plugin_info.install_path.is_dir():
                        plugins.append(plugin_info)

        return plugins

    def _matches_current_project(self, project_path: str | None) -> bool:
        """Check if project_path matches current project root."""
        if not project_path or not self.project_root:
            return False
        try:
            return Path(project_path).resolve() == self.project_root.resolve()
        except OSError:
            return False

    def refresh(self) -> None:
        """Clear cached registry to force reload."""
        self._registry = None

    def get_plugin_source_path(self, plugin_id: str) -> Path | None:
        """Get the source path for a plugin.

        For directory-source plugins: resolves the actual plugin source path by:
        1. Getting marketplace root from known_marketplaces.json
        2. Reading marketplace.json to find the plugin's relative source path
        3. Returning the resolved absolute path

        For other plugins: returns the installPath from installed_plugins.json

        Args:
            plugin_id: Plugin identifier (e.g., "handbook@cc-handbook")

        Returns:
            Path to the plugin source, or None if not found
        """
        parts = plugin_id.split("@") if "@" in plugin_id else [plugin_id]
        plugin_name = parts[0]
        marketplace_name = parts[-1] if len(parts) > 1 else None

        if marketplace_name:
            marketplace_info = self._load_marketplace_info(marketplace_name)
            if marketplace_info:
                source = marketplace_info.get("source", {})
                if source.get("source") == "directory":
                    marketplace_root_str = source.get("path")
                    if marketplace_root_str:
                        marketplace_root = Path(marketplace_root_str)
                        plugin_source = self._find_plugin_source_in_marketplace(
                            marketplace_root, plugin_name
                        )
                        if plugin_source:
                            return plugin_source

        # Fallback to install path from V2 registry
        registry = self.load_registry()
        installations = registry.installed.get(plugin_id, [])
        if installations:
            return Path(installations[0].install_path)

        return None

    def _find_plugin_source_in_marketplace(
        self, marketplace_root: Path, plugin_name: str
    ) -> Path | None:
        """Find a plugin's source path within a marketplace.

        Reads the marketplace.json file and locates the plugin by name.

        Args:
            marketplace_root: Root directory of the marketplace
            plugin_name: Name of the plugin to find

        Returns:
            Resolved absolute path to the plugin source, or None if not found
        """
        marketplace_json = marketplace_root / ".claude-plugin" / "marketplace.json"
        if not marketplace_json.is_file():
            return marketplace_root

        try:
            data = json.loads(marketplace_json.read_text(encoding="utf-8"))
            plugins = data.get("plugins", [])

            for plugin in plugins:
                if plugin.get("name") == plugin_name:
                    source_relative: str = plugin.get("source", "")
                    if source_relative:
                        resolved = (marketplace_root / source_relative).resolve()
                        if resolved.is_dir():
                            return resolved

        except (json.JSONDecodeError, OSError):
            pass

        return marketplace_root

    def _load_marketplace_info(self, marketplace_name: str) -> dict[str, Any] | None:
        """Load marketplace info from known_marketplaces.json."""
        marketplaces_file = (
            self.user_config_path / "plugins" / "known_marketplaces.json"
        )
        if not marketplaces_file.is_file():
            return None
        try:
            data = json.loads(marketplaces_file.read_text(encoding="utf-8"))
            result: dict[str, Any] | None = data.get(marketplace_name)
            return result
        except (json.JSONDecodeError, OSError):
            return None

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
        self,
        plugin_id: str,
        installation: PluginInstallation,
        scope_type: str,
    ) -> PluginInfo | None:
        """Create PluginInfo from V2 installation data.

        Args:
            plugin_id: Plugin identifier
            installation: Installation data from registry
            scope_type: One of "user", "project", or "local"
        """
        if not installation.install_path:
            return None

        short_name = plugin_id.split("@")[0] if "@" in plugin_id else plugin_id
        install_path = Path(installation.install_path)
        version = installation.version

        if not install_path.is_dir() and install_path.parent.is_dir():
            install_path = self._find_latest_version_dir(install_path.parent)
            version = install_path.name

        # Determine enabled status based on scope
        is_enabled = True
        if self._registry:
            if scope_type == "project":
                is_enabled = self._registry.project_enabled.get(plugin_id, True)
            elif scope_type == "local":
                is_enabled = self._registry.local_enabled.get(plugin_id, True)
            else:
                is_enabled = self._registry.user_enabled.get(plugin_id, True)

        scope_map = {
            "user": PluginScope.USER,
            "project": PluginScope.PROJECT,
            "local": PluginScope.PROJECT_LOCAL,
        }
        scope = scope_map[scope_type]
        project_path = (
            Path(installation.project_path) if installation.project_path else None
        )

        return PluginInfo(
            plugin_id=plugin_id,
            short_name=short_name,
            version=version,
            install_path=install_path,
            is_local=installation.is_local,
            is_enabled=is_enabled,
            scope=scope,
            project_path=project_path,
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
