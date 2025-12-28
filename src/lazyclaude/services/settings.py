"""Settings persistence service."""

import json
from pathlib import Path
from typing import Any

from lazyclaude.models.settings import AppSettings

DEFAULT_SUGGESTED_MARKETPLACES: dict[str, dict[str, Any]] = {
    "anthropics/claude-plugins-official": {"tags": ["official"], "stars": 854},
    "NikiforovAll/claude-code-rules": {"tags": ["best-practices"], "stars": 46},
    "SawyerHood/dev-browser": {"tags": ["browser-automation"], "stars": 1511},
    "Piebald-AI/claude-code-lsps": {"tags": ["lsp"], "stars": 57},
    "wshobson/agents": {"tags": ["multi-agent", "orchestration"], "stars": 23707},
    "davila7/claude-code-templates": {"tags": ["templates", "cli"], "stars": 13961},
    "ComposioHQ/awesome-claude-skills": {"tags": ["skills", "curated"], "stars": 12283},
    "steveyegge/beads": {"tags": ["memory", "context"], "stars": 6571},
    "ccplugins/awesome-claude-code-plugins": {
        "tags": ["plugins", "curated"],
        "stars": 151,
    },
}


class SettingsService:
    """Loads and saves application settings."""

    def __init__(self, settings_path: Path | None = None) -> None:
        self._settings_path = settings_path or (
            Path.home() / ".lazyclaude" / "settings.json"
        )

    @property
    def settings_path(self) -> Path:
        """Return the settings file path."""
        return self._settings_path

    def load(self) -> AppSettings:
        """Load settings from file, returning defaults if not found or invalid."""
        if not self._settings_path.is_file():
            return AppSettings()

        try:
            data = json.loads(self._settings_path.read_text(encoding="utf-8"))
            return AppSettings(
                theme=data.get("theme", AppSettings.theme),
                marketplace_auto_collapse=data.get(
                    "marketplace_auto_collapse",
                    AppSettings.marketplace_auto_collapse,
                ),
                suggested_marketplaces=data.get("suggested_marketplaces", {}),
            )
        except (json.JSONDecodeError, OSError):
            return AppSettings()

    def save(self, settings: AppSettings) -> None:
        """Save settings to file, creating directory if needed."""
        try:
            self._settings_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "theme": settings.theme,
                "marketplace_auto_collapse": settings.marketplace_auto_collapse,
                "suggested_marketplaces": settings.suggested_marketplaces,
            }
            self._settings_path.write_text(
                json.dumps(data, indent=2) + "\n",
                encoding="utf-8",
            )
        except OSError:
            pass

    def ensure_suggested_marketplaces(self, settings: AppSettings) -> AppSettings:
        """Ensure default suggested marketplaces exist and are up-to-date.

        This method handles graceful migration of marketplace metadata:
        - Adds new default marketplaces that don't exist in user settings
        - Updates existing entries when DEFAULT_SUGGESTED_MARKETPLACES changes
        - Preserves user-added marketplaces (not in defaults)

        To update marketplace metadata in future versions:
        1. Modify DEFAULT_SUGGESTED_MARKETPLACES with new structure/values
        2. This method auto-detects changes via deep comparison
        3. User settings are updated on next app startup

        The comparison is structure-agnostic: any field change triggers update.
        """
        updated = False
        for repo, default_data in DEFAULT_SUGGESTED_MARKETPLACES.items():
            existing = settings.suggested_marketplaces.get(repo)
            if existing is None or self._marketplace_needs_update(
                existing, default_data
            ):
                settings.suggested_marketplaces[repo] = default_data
                updated = True
        if updated:
            self.save(settings)
        return settings

    def _marketplace_needs_update(
        self, existing: dict[str, Any], default: dict[str, Any]
    ) -> bool:
        """Check if marketplace entry needs update via deep equality comparison.

        Uses Python's built-in dict comparison which recursively compares:
        - All keys present in both dicts
        - All values (including nested dicts/lists)

        This handles any future schema changes automatically - just update
        DEFAULT_SUGGESTED_MARKETPLACES and existing user entries will be migrated.
        """
        return existing != default
