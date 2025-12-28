"""Application settings model."""

from dataclasses import dataclass, field
from typing import Any

from lazyclaude.themes import DEFAULT_THEME


@dataclass
class AppSettings:
    """Persistent application settings."""

    theme: str = DEFAULT_THEME
    marketplace_auto_collapse: bool = True
    suggested_marketplaces: dict[str, dict[str, Any]] = field(default_factory=dict)
