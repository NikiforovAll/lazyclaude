"""Data models for marketplace plugins."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class MarketplaceSource:
    """Source configuration for a marketplace."""

    source_type: str  # "github" or "directory"
    repo: str | None = None
    path: str | None = None


@dataclass
class MarketplaceEntry:
    """A marketplace entry from known_marketplaces.json."""

    name: str
    source: MarketplaceSource
    install_location: Path
    last_updated: str | None = None


@dataclass
class MarketplacePlugin:
    """A plugin available in a marketplace."""

    name: str
    description: str
    source: str
    marketplace_name: str
    full_plugin_id: str
    is_installed: bool = False
    is_enabled: bool = True
    install_path: Path | None = None
    installed_version: str | None = None
    extra_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Marketplace:
    """A fully loaded marketplace with its plugins."""

    entry: MarketplaceEntry
    plugins: list[MarketplacePlugin] = field(default_factory=list)
    error: str | None = None
