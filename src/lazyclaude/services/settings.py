"""Settings persistence service."""

import json
from pathlib import Path

from lazyclaude.models.settings import AppSettings


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
            return AppSettings(theme=data.get("theme", AppSettings.theme))
        except (json.JSONDecodeError, OSError):
            return AppSettings()

    def save(self, settings: AppSettings) -> None:
        """Save settings to file, creating directory if needed."""
        try:
            self._settings_path.parent.mkdir(parents=True, exist_ok=True)
            data = {"theme": settings.theme}
            self._settings_path.write_text(
                json.dumps(data, indent=2) + "\n",
                encoding="utf-8",
            )
        except OSError:
            pass
