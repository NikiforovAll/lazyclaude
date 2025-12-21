"""Service for loading marketplace data."""

import json
from pathlib import Path

from lazyclaude.models.marketplace import (
    Marketplace,
    MarketplaceEntry,
    MarketplacePlugin,
    MarketplaceSource,
)
from lazyclaude.services.plugin_loader import PluginLoader


class MarketplaceLoader:
    """Loads marketplace and plugin data from the filesystem."""

    def __init__(
        self,
        user_config_path: Path | None = None,
        plugin_loader: PluginLoader | None = None,
    ) -> None:
        self.user_config_path = user_config_path or Path.home() / ".claude"
        self._plugin_loader = plugin_loader
        self._installed_plugin_ids: set[str] | None = None
        self._enabled_plugin_ids: set[str] | None = None
        self._install_paths: dict[str, Path] | None = None
        self._marketplaces_cache: list[Marketplace] | None = None

    def load_marketplaces(self) -> list[Marketplace]:
        """Load all marketplaces from known_marketplaces.json."""
        if self._marketplaces_cache is not None:
            return self._marketplaces_cache

        marketplaces: list[Marketplace] = []
        known_file = self.user_config_path / "plugins" / "known_marketplaces.json"

        if not known_file.is_file():
            return marketplaces

        try:
            data = json.loads(known_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return marketplaces

        self._load_installed_plugins()

        for name, entry_data in data.items():
            entry = self._parse_marketplace_entry(name, entry_data)
            if entry:
                marketplace = self._load_marketplace(entry)
                marketplaces.append(marketplace)

        self._marketplaces_cache = marketplaces
        return marketplaces

    def _parse_marketplace_entry(
        self, name: str, data: dict
    ) -> MarketplaceEntry | None:
        """Parse a single marketplace entry from known_marketplaces.json."""
        source_data = data.get("source", {})
        source_type = source_data.get("source", "unknown")

        source = MarketplaceSource(
            source_type=source_type,
            repo=source_data.get("repo"),
            path=source_data.get("path"),
        )

        install_location = data.get("installLocation")
        if not install_location:
            return None

        return MarketplaceEntry(
            name=name,
            source=source,
            install_location=Path(install_location),
            last_updated=data.get("lastUpdated"),
        )

    def _load_marketplace(self, entry: MarketplaceEntry) -> Marketplace:
        """Load a marketplace's plugins from its marketplace.json."""
        marketplace_json = (
            entry.install_location / ".claude-plugin" / "marketplace.json"
        )

        if not marketplace_json.is_file():
            return Marketplace(
                entry=entry,
                error=f"marketplace.json not found at {marketplace_json}",
            )

        try:
            data = json.loads(marketplace_json.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            return Marketplace(entry=entry, error=str(e))

        plugins: list[MarketplacePlugin] = []
        for plugin_data in data.get("plugins", []):
            plugin = self._parse_plugin(plugin_data, entry.name)
            if plugin:
                plugins.append(plugin)

        return Marketplace(entry=entry, plugins=plugins)

    def _parse_plugin(
        self, data: dict, marketplace_name: str
    ) -> MarketplacePlugin | None:
        """Parse a single plugin from marketplace.json."""
        name = data.get("name")
        if not name:
            return None

        full_id = f"{name}@{marketplace_name}"
        is_installed = full_id in (self._installed_plugin_ids or set())
        is_enabled = full_id in (self._enabled_plugin_ids or set())

        source = data.get("source", "")
        if isinstance(source, dict):
            source = source.get("url", str(source))

        install_path = (self._install_paths or {}).get(full_id)

        return MarketplacePlugin(
            name=name,
            description=data.get("description", ""),
            source=source,
            marketplace_name=marketplace_name,
            full_plugin_id=full_id,
            is_installed=is_installed,
            is_enabled=is_enabled if is_installed else True,
            install_path=install_path,
            extra_metadata={
                k: v
                for k, v in data.items()
                if k not in ("name", "description", "source")
            },
        )

    def _load_installed_plugins(self) -> None:
        """Load set of installed and enabled plugin IDs."""
        if self._plugin_loader:
            registry = self._plugin_loader.load_registry()
            self._installed_plugin_ids = set(registry.installed.keys())
            enabled_in_user = {
                pid for pid, enabled in registry.user_enabled.items() if enabled
            }
            enabled_in_project = {
                pid for pid, enabled in registry.project_enabled.items() if enabled
            }
            enabled_in_local = {
                pid for pid, enabled in registry.local_enabled.items() if enabled
            }
            self._enabled_plugin_ids = (
                (
                    self._installed_plugin_ids
                    - {
                        pid
                        for pid, enabled in {
                            **registry.user_enabled,
                            **registry.project_enabled,
                            **registry.local_enabled,
                        }.items()
                        if not enabled
                    }
                )
                | enabled_in_user
                | enabled_in_project
                | enabled_in_local
            )
            self._install_paths = {}
            for pid, installations in registry.installed.items():
                if installations:
                    self._install_paths[pid] = Path(installations[0].install_path)
        else:
            self._installed_plugin_ids = set()
            self._enabled_plugin_ids = set()
            self._install_paths = {}

    def get_plugin_source_dir(self, plugin: MarketplacePlugin) -> Path | None:
        """Get the source directory for a plugin (installed or from marketplace)."""
        if plugin.install_path:
            if plugin.install_path.exists():
                return plugin.install_path
            if plugin.install_path.parent.exists():
                latest = self._find_latest_version_dir(plugin.install_path.parent)
                if latest and latest.exists():
                    return latest

        marketplace = self._find_marketplace(plugin.marketplace_name)
        if marketplace:
            plugin_dir = (marketplace.entry.install_location / plugin.source).resolve()
            if plugin_dir.exists():
                return plugin_dir
        return None

    def _find_latest_version_dir(self, parent_dir: Path) -> Path | None:
        """Find the latest version directory in a plugin parent directory."""
        try:
            subdirs = [d for d in parent_dir.iterdir() if d.is_dir()]
            if subdirs:
                return max(subdirs, key=lambda d: self._parse_version(d.name))
        except OSError:
            pass
        return None

    @staticmethod
    def _parse_version(version_str: str) -> tuple[int, ...] | tuple[str]:
        """Parse version string into comparable tuple."""
        try:
            return tuple(int(part) for part in version_str.split("."))
        except ValueError:
            return (version_str,)

    def _find_marketplace(self, marketplace_name: str) -> Marketplace | None:
        """Find a marketplace by name."""
        marketplaces = self.load_marketplaces()
        for marketplace in marketplaces:
            if marketplace.entry.name == marketplace_name:
                return marketplace
        return None

    def refresh(self) -> None:
        """Clear cache to force reload."""
        self._installed_plugin_ids = None
        self._enabled_plugin_ids = None
        self._install_paths = None
        self._marketplaces_cache = None
        if self._plugin_loader:
            self._plugin_loader._registry = None
