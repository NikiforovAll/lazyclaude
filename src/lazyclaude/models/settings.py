"""Application settings model."""

from dataclasses import dataclass

from lazyclaude.themes import DEFAULT_THEME


@dataclass
class AppSettings:
    """Persistent application settings."""

    theme: str = DEFAULT_THEME
